"""Checkpoint-specific, fixed-cohort diagnostics for three existing hypotheses."""

import argparse
import ast
import copy
from datetime import datetime, timezone
import fcntl
import importlib.util
import json
import logging
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("immutable_native", args.runner)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    assert native.digest(args.runner) == "f29e5f8dd8dd70a8cb7428f8facd7f8e37401ced27e01cdf1e0ef2db19c175e9"
    torch = native.torch
    root = Path("/data3/songcl/Project/Cluster_project/Cluster")
    pipe = root.parent / "pipeline"
    output = Path(args.output)
    old = pipe / "diagnostics/bps_population_f8bdf4cb21774bf2af11f959fa12d89a"
    locks = []
    rows = []
    try:
        for name in ("/tmp/cluster_project_gpu7_exclusive.lock",
                     "/tmp/cluster_project_gpu7_diagnostic.lock",
                     "/tmp/cluster_project_gpu7_slot2_diagnostic.lock"):
            handle = open(name, "a+b")
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locks.append(handle)
        first_guard = native.guard(root)
        torch.cuda.set_per_process_memory_fraction(.25, 0)
        sys.path[:0] = [str(root), str(root / "framework/lib")]
        import gorilla
        from framework import resolve_network
        from framework.dataset import build_dataset

        config = "configs/Quard/bps/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps.yaml"
        cfg = gorilla.Config.fromfile(str(root / config))
        assert cfg.train.seed == 1999 and cfg.train.epochs == 50 and cfg.lr_scheduler.max_iters == 70
        checkpoint = old / "checkpoint_snapshot.pth"
        assert native.digest(checkpoint) == "f17f2ec3b08422f033a6683a4030bff1d69a1112514c6ac96dcb38870be735fd"
        saved = torch.load(checkpoint, map_location="cpu", weights_only=False, mmap=True)
        gorilla.set_random_seed(1999)
        model = resolve_network(config)(**cfg.model)
        state = saved["model"]
        keys = ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids")
        assert set(state) - set(model.state_dict()) == set(keys)
        buffers = dict(model.named_buffers())
        buffer_audit = {}
        for key in keys:
            assert key in buffers and key not in model.state_dict()
            left, right = state[key].detach().cpu(), buffers[key].detach().cpu()
            assert left.shape == right.shape and left.dtype == right.dtype and torch.equal(left, right)
            buffer_audit[key] = native.input_hash(left)
        filtered = {key: value for key, value in state.items() if key not in keys}
        model.load_state_dict(filtered, strict=True)
        model.cuda().train()
        manifest = json.loads((old / "source_manifest.json").read_text())
        folder = root / "framework/model/Quard_model" / native.PACKAGE
        for name, expected in manifest["package"].items():
            assert native.digest(folder / name) == expected
        dataset = build_dataset(cfg.data.train, logging.getLogger("bps-scalar-checkpoint"))
        generator_path = pipe / "native_role_direction_v2_20261014_0010.py"
        assert native.digest(generator_path) == "c5a9c1157421bd9cc386a2da160ac1cf0ae376948ddff5b7f0c6808be690d749"
        generator = next(node for node in ast.parse(generator_path.read_text()).body
                         if isinstance(node, ast.FunctionDef) and node.name == "logit_functions")
        namespace = {"ast": ast, "copy": copy}
        exec(compile(ast.Module(body=[generator], type_ignores=[]), str(generator_path), "exec"), namespace)
        functions = namespace["logit_functions"](folder / "loss.py", model.criterion, torch)
        cohort, source_hashes = {}, {}
        for family, filename, expected in (
            ("role", "role_gradient_native_20261013_1012.json",
             "ca0697d740a4d239dfe4465542ac75beed09a0d95b963022fc7b796ec6368187"),
            ("relation", "relation_gradient_native_20261013_0707.json",
             "f98351adaf132046fca6ca11158a89a21ca8e0fc5a223d635cf3207b214eb7d4"),
        ):
            source = pipe / filename
            assert native.digest(source) == expected
            source_hashes[filename] = expected
            for row in json.loads(source.read_text())["rows"]:
                if row["trial"] != 0:
                    continue
                selection = row["selection"]
                group = selection["group"]
                if group not in cohort:
                    cohort[group] = dict(group=group, scene=selection["scene"],
                                         ann_ids=row["ann_ids"], families=[])
                assert cohort[group]["ann_ids"] == row["ann_ids"]
                cohort[group]["families"].append(family)
        semantic = model.criterion.loss_sem_align
        calls, held = [], {}

        def capture(*values):
            actual = semantic(*values)
            calls.append((values, actual))
            return actual

        model.criterion.loss_sem_align = capture
        hook = model.criterion.register_forward_pre_hook(lambda module, inputs: held.update(pred=inputs[0]))
        try:
            for selection in cohort.values():
                native.guard(root)
                gorilla.set_random_seed(1999)
                batch = dataset.collate_fn([dataset[selection["group"]]])
                assert list(map(int, batch["ann_ids"])) == selection["ann_ids"]
                fingerprint = native.input_hash(batch)
                trials, previous_masks, previous_gradients = [], None, None
                max_mask_delta = max_gradient_delta = 0.0
                for trial in range(2):
                    model.load_state_dict(filtered, strict=True)
                    model.train()
                    gorilla.set_random_seed(1999)
                    calls.clear()
                    held.clear()
                    with torch.no_grad():
                        full_loss, _ = model(batch, mode="loss")
                    pred = held["pred"]
                    final = [(values, actual) for values, actual in calls
                             if values[0] is pred["proj_tokens"] and values[1] is pred["proj_queries"]]
                    assert len(final) == 1, "Final semantic tensor identity ambiguous"
                    values, actual = final[0]
                    tokens, queries, language, targets, indices, num_boxes = values
                    raw = (queries.detach() @ tokens.detach().transpose(-1, -2)) / model.criterion.temperature
                    subset = {key: torch.zeros_like(raw, dtype=torch.bool)
                              for key in ("main_secondary", "relation_other", "fractional_secondary")}
                    relation_targets = []
                    for bi, (target, (src, tgt)) in enumerate(zip(targets, indices)):
                        maps = {name: target[name][tgt, :raw.shape[-1]] for name in (
                            "positive_map", "modify_positive_map", "pron_positive_map",
                            "rel_positive_map", "other_entity_map")}
                        secondary = [maps[key] for key in ("modify_positive_map", "pron_positive_map", "rel_positive_map")]
                        subset["main_secondary"][bi, src] = (maps["positive_map"] > 0) & (
                            (secondary[0] > 0) | (secondary[1] > 0) | (secondary[2] > 0))
                        subset["relation_other"][bi, src] = (maps["rel_positive_map"] > 0) & (maps["other_entity_map"] > 0)
                        subset["fractional_secondary"][bi, src] = (
                            ((secondary[0] > 0) & (secondary[0] < 1)) |
                            ((secondary[1] > 0) & (secondary[1] < 1)) |
                            ((secondary[2] > 0) & (secondary[2] < 1)))
                        edited = dict(target)
                        edited["other_entity_map"] = target["other_entity_map"].clone()
                        edited["other_entity_map"].masked_fill_(target["rel_positive_map"] > 0, 0)
                        relation_targets.append(edited)
                    conditions, gradients = {}, {}
                    with torch.enable_grad():
                        for name in ("original", "identity", "precedence", "mass", "relation_overlap_removed"):
                            z = raw.detach().clone().requires_grad_(True)
                            inputs = list(values)
                            if name == "relation_overlap_removed":
                                inputs[3] = relation_targets
                            operator = functions["original" if name == "relation_overlap_removed" else name]
                            value = operator(*inputs, z)
                            gradient = torch.autograd.grad(value, z)[0].detach()
                            assert bool(torch.isfinite(value).all() and torch.isfinite(gradient).all())
                            gradients[name] = gradient.cpu()
                            conditions[name] = {"loss": float(value.detach()), "subsets": {
                                key: {
                                    "count": int(mask.sum()),
                                    "attracting": int((gradient[mask] < 0).sum()),
                                    "repelling": int((gradient[mask] > 0).sum()),
                                    "zero": int((gradient[mask] == 0).sum()),
                                } for key, mask in subset.items()
                            }}
                    for name in conditions:
                        conditions[name]["loss_delta_from_original"] = conditions[name]["loss"] - conditions["original"]["loss"]
                        conditions[name]["subset_sign_flips"] = {
                            key: int(((gradients[name].sign() != gradients["original"].sign()) & mask.cpu()).sum())
                            for key, mask in subset.items()
                        }
                    identity_delta = max(abs(conditions["identity"]["loss"] - conditions["original"]["loss"]),
                                         float((gradients["identity"] - gradients["original"]).abs().max()))
                    assert identity_delta == 0
                    masks = [value.detach().cpu().clone() for value in pred["masks"]]
                    if previous_masks is not None:
                        max_mask_delta = max(float((a - b).abs().max()) for a, b in zip(previous_masks, masks))
                        max_gradient_delta = max(float((previous_gradients[name] - gradients[name]).abs().max()) for name in gradients)
                    previous_masks, previous_gradients = masks, gradients
                    trials.append({"full_loss": float(full_loss), "native_semantic_loss": float(actual),
                                   "source_loss_identity_abs_delta": abs(float(actual) - conditions["original"]["loss"]),
                                   "conditions": conditions})
                    assert native.input_hash(batch) == fingerprint
                row = {"selection": selection, "input_sha256": fingerprint, "trials": trials,
                       "max_mask_repeat_delta": max_mask_delta, "max_gradient_repeat_delta": max_gradient_delta,
                       "full_loss_repeat_delta": abs(trials[0]["full_loss"] - trials[1]["full_loss"]),
                       "pass_repeat1e6": max(max_mask_delta, max_gradient_delta,
                                            abs(trials[0]["full_loss"] - trials[1]["full_loss"])) <= 1e-6,
                       "pass_native_identity1e6": max(t["source_loss_identity_abs_delta"] for t in trials) <= 1e-6}
                rows.append(row)
                native.save(output, {"token": args.token, "complete": False, "rows": rows})
                print("completed scalar group " + str(selection["group"]), flush=True)
                torch.cuda.empty_cache()
        finally:
            hook.remove()
            model.criterion.loss_sem_align = semantic
        native.save(output, {
            "token": args.token, "complete": True, "rows": rows,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "script_sha256": native.digest(__file__), "source_hashes": source_hashes,
            "checkpoint_sha256": native.digest(checkpoint), "checkpoint_meta": saved.get("meta", {}),
            "buffer_audit": buffer_audit, "guard_before": first_guard, "guard_after": native.guard(root),
            "peak_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
            "optimizer_steps": 0, "model_parameter_backward": 0,
            "scope": "New BPS checkpoint-specific frozen TRAIN logit diagnostics only; not full-model intervention, historical repeat repair, independent core, task harm, efficacy or admission.",
        })
    finally:
        for handle in reversed(locks):
            fcntl.flock(handle, fcntl.LOCK_UN)
            handle.close()


if __name__ == "__main__":
    main()
