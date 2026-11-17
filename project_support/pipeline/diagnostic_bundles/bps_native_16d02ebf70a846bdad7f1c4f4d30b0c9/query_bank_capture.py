"""Add native-bank readouts to immutable V3 without altering its returned loss."""

import argparse
import ast
import hashlib
import importlib
import json
from pathlib import Path
import sys

BANK = {"rows": [], "installed": []}


def install_bank_capture(model, native):
    if any(model is item[0] for item in BANK["installed"]):
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
        expressions = []
        matched_sum = 0.0
        for expression, (mask, target, index, support, indi) in enumerate(
                zip(masks, targets, indices, supports, pred["indis"])):
            assert torch.equal(target["masks"], target["masks"][:1].expand_as(target["masks"]))
            gt = target["masks"][0]
            iou = module.get_iou(mask, gt)
            selected = int(indi.detach().softmax(-1)[:, 1].argmax())
            row = {"expression": expression, "query_count": len(mask),
                   "selected_query": selected, "selected_iou": float(iou[selected]),
                   "bank_best_iou": float(iou.max()), "ious": iou.detach().cpu().tolist(),
                   "matched_queries": index[0].tolist(), "available_events": len(support["costs"])}
            if support["costs"]:
                counts = support["counts"].to(mask.device)
                probability = mask.sigmoid().double() * counts
                probability /= probability.sum(-1, keepdim=True).clamp_min(1e-12)
                teacher = gt.double() * counts
                assert teacher.sum() > 0
                teacher /= teacher.sum()
                events, oracles = [], []
                for cost in support["costs"]:
                    cost = cost.to(mask.device)
                    gt_expected = teacher @ cost
                    excess = torch.relu(probability @ cost - gt_expected)
                    events.append(excess.min(-1).values)
                    keep = gt_expected == gt_expected.min()
                    oracles.append(excess[:, keep].min(-1).values)
                    assert bool((torch.relu(teacher @ cost - gt_expected) == 0).all())
                normal = torch.stack(events, dim=-1).mean(-1)
                oracle = torch.stack(oracles, dim=-1).mean(-1)
                assert bool(torch.isfinite(normal).all() and torch.isfinite(oracle).all())
                matched_sum += float(normal[index[0]].sum())
                row.update(original=normal.detach().cpu().tolist(),
                           oracle=oracle.detach().cpu().tolist(),
                           selected_original=float(normal[selected]), selected_oracle=float(oracle[selected]),
                           low_iou_queries=int((iou < .5).sum()),
                           gt_self_control="algebraic_zero_not_efficacy")
            expressions.append(row)
        BANK["rows"].append({
            "expressions": expressions, "original_component": float(actual),
            "matched_vector_component": matched_sum / float(num_boxes),
            "component_identity_abs_delta": abs(float(actual) - matched_sum / float(num_boxes)),
        })
        return actual

    module.support_excess = capture
    BANK["installed"].append((model, module, original, hook))


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--adapter", required=True)
    own, rest = parser.parse_known_args()
    output_parser = argparse.ArgumentParser(add_help=False)
    output_parser.add_argument("--output", required=True)
    output_args, _ = output_parser.parse_known_args(rest)
    adapter = Path(own.adapter)
    assert hashlib.sha256(adapter.read_bytes()).hexdigest() == (
        "aa2b164502ab3011023b4b45d65a7423fc3c9cd7e6f5544ccd53f8ae17190508"
    )
    source = ast.parse(adapter.read_text())
    strict_load = next(node for node in ast.walk(source)
                       if isinstance(node, ast.FunctionDef) and node.name == "strict_state_load")
    injected = 0
    for node in ast.walk(strict_load):
        if isinstance(node, ast.If):
            for index, statement in enumerate(node.body):
                if (isinstance(statement, ast.Assign) and isinstance(statement.targets[0], ast.Name)
                        and statement.targets[0].id == "result"):
                    node.body[index + 1:index + 1] = ast.parse("install_bank_capture(module, native)").body
                    injected += 1
    assert injected == 1
    original_argv = sys.argv
    sys.argv = [original_argv[0], *rest]
    status = "failed"
    try:
        namespace = {"__name__": "__main__", "__file__": str(adapter),
                     "install_bank_capture": install_bank_capture}
        exec(compile(ast.fix_missing_locations(source), str(adapter), "exec"), namespace)
        status = "completed"
    finally:
        sys.argv = original_argv
        native = None
        for model, module, original, hook in reversed(BANK["installed"]):
            hook.remove()
            module.support_excess = original
        bank_output = Path(output_args.output).parent / "bank_result.json"
        temporary = bank_output.with_suffix(".tmp")
        temporary.write_text(json.dumps({
            "status": status, "rows": BANK["rows"],
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "adapter_sha256": hashlib.sha256(adapter.read_bytes()).hexdigest(),
            "scope": "Native TRAIN query-bank readout only; selected TRAIN head, not deployed VAL. Oracle not a verified witness, deployable repair, causal harm or trained efficacy.",
        }, indent=2) + "\n")
        temporary.replace(bank_output)


if __name__ == "__main__":
    main()
