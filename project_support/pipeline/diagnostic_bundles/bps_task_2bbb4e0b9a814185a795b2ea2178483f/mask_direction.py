"""Isolated native-mask gradients; original relation loss is returned unchanged."""

import argparse
import ast
import hashlib
import importlib
import json
from pathlib import Path
import sys

STATE = {"installed": [], "rows": [], "previous_gradients": None}
BASE = Path("/data3/songcl/Project/Cluster_project/pipeline/diagnostics")
OLD = BASE / "bps_population_f8bdf4cb21774bf2af11f959fa12d89a"
ADAPTER = BASE / "bps_native_16d02ebf70a846bdad7f1c4f4d30b0c9/native_capture_v3.py"


def install(model, native):
    if any(model is item[0] for item in STATE["installed"]):
        return
    torch = native.torch
    module = importlib.import_module(type(model.criterion).__module__)
    original = module.support_excess
    held = {}
    hook = model.criterion.register_forward_pre_hook(lambda criterion, inputs: held.update(pred=inputs[0]))

    def capture(masks, targets, indices, num_boxes, supports, fragmented=False):
        actual = original(masks, targets, indices, num_boxes, supports, fragmented=fragmented)
        pred = held.get("pred")
        if (pred is None or fragmented or len(masks) != len(pred["indis"])
                or any(mask.shape[0] != indi.shape[0] for mask, indi in zip(masks, pred["indis"]))):
            return actual
        assert len(masks) > 1
        restricted = []
        for target, support in zip(targets, supports):
            entry = {**support, "costs": []}
            if support["costs"]:
                assert torch.equal(target["masks"], target["masks"][:1].expand_as(target["masks"]))
                counts = support["counts"].to(masks[0].device)
                teacher = target["masks"][:1].double() * counts
                teacher /= teacher.sum(-1, keepdim=True)
                for field in support["costs"]:
                    expected = teacher @ field.to(teacher.device)
                    keep = (expected[0] == expected[0].min()).cpu()
                    entry["costs"].append(field[:, keep])
            restricted.append(entry)
        scores = pred["scores"].detach()
        weights = model.criterion.loss_weight

        def task(values):
            bce, dice, _ = model.criterion.loss_masks(values, scores, targets, indices, num_boxes)
            return weights[0] * bce + weights[1] * dice

        conditions, gradients, expressions = {}, {}, []
        with torch.enable_grad():
            reference = [mask.detach().clone().requires_grad_(True) for mask in masks]
            task_value = task(reference)
            task_gradient = torch.autograd.grad(task_value.sum(), reference)
            for name, geometry in (("original", supports), ("identity", supports), ("oracle", restricted)):
                values = [mask.detach().clone().requires_grad_(True) for mask in masks]
                value = original(values, targets, indices, num_boxes, geometry)
                gradient = torch.autograd.grad(value.sum(), values)
                assert bool(torch.isfinite(value).all()) and all(bool(torch.isfinite(g).all()) for g in gradient)
                gradients[name] = [g.detach().cpu() for g in gradient]
                norm = sum(float(g.double().square().sum()) for g in gradient) ** .5
                dot = sum(float((g.double() * t.double()).sum()) for g, t in zip(gradient, task_gradient))
                record = {"loss": float(value.detach()), "gradient_norm": norm, "task_dot": dot}
                with torch.no_grad():
                    baseline = float(task([mask.detach() for mask in masks]))
                    assert baseline == float(task([mask.detach() for mask in masks]))
                    if norm:
                        direction = [g / norm for g in gradient]
                        descent = float(task([mask.detach() - .001 * d for mask, d in zip(masks, direction)]))
                        ascent = float(task([mask.detach() + .001 * d for mask, d in zip(masks, direction)]))
                        central = (descent - ascent) / .002
                        analytic = -dot / norm
                        record.update(
                            descent_task_delta=descent - baseline, ascent_task_delta=ascent - baseline,
                            central_descent_derivative=central, analytic_descent_derivative=analytic,
                            finite_difference_abs_error=abs(central - analytic),
                            pass_derivative1e6=abs(central - analytic) <= 1e-6,
                        )
                    else:
                        record.update(status="zero_gradient_not_active_control", pass_derivative1e6=None)
                conditions[name] = record
            assert conditions["original"] == conditions["identity"]
            assert all(torch.equal(a, b) for a, b in zip(gradients["original"], gradients["identity"]))
            for bi, (mask, target, (src, tgt), support) in enumerate(zip(masks, targets, indices, supports)):
                ious = module.get_iou(mask[src], target["masks"][tgt])
                for local, (q, g) in enumerate(zip(src.tolist(), tgt.tolist())):
                    expressions.append({
                        "expression": bi, "query": q, "target": g, "iou": float(ious[local]),
                        "available_events": len(support["costs"]),
                        "conditions": {
                            name: {
                                "mask_gradient_norm": float(gradient[bi][q].double().norm()),
                                "task_dot": float((gradient[bi][q].double() * task_gradient[bi][q].detach().cpu().double()).sum()),
                            } for name, gradient in gradients.items()
                        },
                    })
        assert all(parameter.grad is None for parameter in model.parameters())
        row = {
            "native_original_component": float(actual),
            "component_identity_abs_delta": abs(float(actual) - conditions["original"]["loss"]),
            "task_loss": float(task_value.detach()), "conditions": conditions,
            "matched_queries": expressions, "epsilon": .001,
        }
        if len(STATE["rows"]) % 2 == 0:
            STATE["previous_gradients"] = gradients
        else:
            row["gradient_repeat_max_delta"] = max(
                float((a - b).abs().max()) for name in gradients
                for a, b in zip(STATE["previous_gradients"][name], gradients[name])
            )
            STATE["previous_gradients"] = None
        STATE["rows"].append(row)
        return actual

    module.support_excess = capture
    STATE["installed"].append((model, module, original, hook))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    assert hashlib.sha256(ADAPTER.read_bytes()).hexdigest() == "aa2b164502ab3011023b4b45d65a7423fc3c9cd7e6f5544ccd53f8ae17190508"
    output = Path(args.output)
    native_dir = output.parent / "mask_native"
    native_dir.mkdir(exist_ok=False)
    tree = ast.parse(ADAPTER.read_text())
    function = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "strict_state_load")
    changes = 0
    for node in ast.walk(function):
        if isinstance(node, ast.If):
            for index, statement in enumerate(node.body):
                if (isinstance(statement, ast.Assign) and isinstance(statement.targets[0], ast.Name)
                        and statement.targets[0].id == "result"):
                    node.body[index + 1:index + 1] = ast.parse("install_mask_capture(module, native)").body
                    changes += 1
    assert changes == 1
    previous_argv = sys.argv
    sys.argv = [sys.argv[0], "--runner", args.runner,
                "--code-root", "/data3/songcl/Project/Cluster_project/Cluster",
                "--config", "configs/Quard/bps/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps.yaml",
                "--checkpoint", str(OLD / "checkpoint_snapshot.pth"),
                "--source-manifest", str(OLD / "source_manifest.json"),
                "--population", str(OLD / "result.json"),
                "--output", str(native_dir / "native_result.json"), "--token", args.token]
    status = "failed"
    try:
        exec(compile(ast.fix_missing_locations(tree), str(ADAPTER), "exec"),
             {"__name__": "__main__", "__file__": str(ADAPTER), "install_mask_capture": install})
        status = "completed"
    finally:
        sys.argv = previous_argv
        for model, module, original, hook in reversed(STATE["installed"]):
            hook.remove()
            module.support_excess = original
        result = {
            "token": args.token, "status": status, "rows": STATE["rows"],
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "native_result": json.loads((native_dir / "native_result.json").read_text())
            if (native_dir / "native_result.json").exists() else None,
            "optimizer_steps": 0, "model_parameter_backward_calls": 0,
            "scope": "Local isolated mask-gradient/task-loss readout, not parameter update, global causal harm, VAL, efficacy or oracle repair admission.",
        }
        output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
