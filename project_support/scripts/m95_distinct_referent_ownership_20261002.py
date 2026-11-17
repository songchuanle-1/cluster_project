"""Read-only native same-scene distinct-referent ownership diagnostic."""
import argparse
import importlib
import json
import logging
import os
from pathlib import Path
import sys
import time

from m95_multiword_native_31_20260928 import (
    NAME, CHECKPOINT_SHA, DATASET_SHA, ANNOTATION_SHA, GRAPH_SHA,
    frozen_rows, select_native_indices, selected_loader, sha,
)


def pair_probe(torch, logits, targets):
    """Keep labels fixed; compare actual, independent and axis-broken gradients."""
    if logits.shape != targets.shape or logits.shape[0] != 2:
        raise ValueError("Expected two bound masks on one support")
    if bool((targets[0] & targets[1]).any()) or not bool(targets.all(0).logical_not().any()):
        raise ValueError("Ground-truth ownership overlaps")
    if not bool(targets.any(1).all()):
        raise ValueError("Empty target")
    result = {}
    for arm in ("joint", "independent", "shifted_joint"):
        z = logits.detach().double().requires_grad_(True)
        if arm == "independent":
            loss = torch.nn.functional.binary_cross_entropy_with_logits(z, targets.double())
        else:
            other = z[1].roll(1) if arm == "shifted_joint" else z[1]
            scores = torch.stack((torch.zeros_like(z[0]), z[0], other), dim=-1)
            owner = targets[0].long() + 2 * targets[1].long()
            loss = torch.nn.functional.cross_entropy(scores, owner)
        grad = torch.autograd.grad(loss, z)[0]
        if not bool(torch.isfinite(grad).all()):
            raise ValueError("Nonfinite ownership gradient")
        # Both derivatives use the original, physically bound target masks.
        velocities = [
            float((-grad[k, targets[k]]).mean()
                  - (-grad[k, targets[1 - k]]).mean()) for k in range(2)
        ]
        correction = torch.stack([-targets[k].double() / targets[k].sum()
                                  + targets[1 - k].double() / targets[1 - k].sum()
                                  for k in range(2)])
        result[arm] = {
            "loss": float(loss.detach()), "gradient_norm": float(grad.norm()),
            "margin_velocity": velocities,
            "corrective_cosine": float((grad * correction).sum()
                                      / (grad.norm() * correction.norm())),
        }
    a = logits.detach().double().requires_grad_(True)
    owner = targets[0].long() + 2 * targets[1].long()
    scores = torch.stack((torch.zeros_like(a[0]), a[0], a[1]), dim=-1)
    native_grad = torch.autograd.grad(torch.nn.functional.cross_entropy(scores, owner), a)[0]
    b = logits.detach().double().requires_grad_(True)
    independent_grad = torch.autograd.grad(
        torch.nn.functional.binary_cross_entropy_with_logits(b, targets.double()), b)[0]
    result["joint_independent_gradient_cosine"] = float(
        (native_grad * independent_grad).sum()
        / (native_grad.norm() * independent_grad.norm()))
    return result


def main():
    parser = argparse.ArgumentParser()
    for key in ("root", "checkpoint", "manifest", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    if (os.environ.get("CUDA_VISIBLE_DEVICES") != "7" or output.exists()
            or not output.is_relative_to(root.parent / "pipeline")
            or sha(args.checkpoint) != CHECKPOINT_SHA):
        raise ValueError("GPU7, fresh project output and frozen checkpoint required")
    frozen = frozen_rows(args.manifest)
    data_root = Path("/data3/songcl/data/data_cluster")
    inputs = {
        "dataset": root / "framework/dataset/scannetv2.py",
        "annotations": data_root / "scanrefer/ScanRefer_train_new.json",
        "graphs": data_root / "scanrefer/scene_graphs_new_train.json",
    }
    expected = {"dataset": DATASET_SHA, "annotations": ANNOTATION_SHA, "graphs": GRAPH_SHA}
    if {name: sha(path) for name, path in inputs.items()} != expected:
        raise ValueError("Frozen native sources differ")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import torch
    import gorilla
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader
    from m95_final_seed_target_probe_20260927 import batch_fingerprint

    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.20)
    cfg = gorilla.Config.fromfile(str(root / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")))
    cfg.model.data_root = cfg.data.train.data_root = str(data_root) + "/"
    gorilla.set_random_seed(1999)
    source = build_dataset(cfg.data.train, logging.getLogger("distinct_referent_ownership"))
    indices = select_native_indices(source, frozen)
    model = importlib.import_module("framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    held, matches = {}, []
    original = model.criterion.match_sampled_ins

    def capture_match(*values):
        result = original(*values)
        matches.append(result)
        return result

    model.criterion.match_sampled_ins = capture_match
    handle = model.criterion.register_forward_pre_hook(
        lambda module, values: held.update(pred=values[0], fps=values[7]))
    rows, exclusions, outcomes = [], [], []
    started = time.time()
    try:
        for repeat in range(2):
            gorilla.set_random_seed(1999)
            loader = selected_loader(source, indices, DataLoader)
            for batch_index, batch in enumerate(loader):
                fingerprint = batch_fingerprint(torch, batch)
                held.clear()
                matches.clear()
                gorilla.set_random_seed(1999)
                with torch.no_grad():
                    loss, _ = model(batch, mode="loss")
                pred = held["pred"]
                count = len(batch["ann_ids"])
                if len(batch["scan_ids"]) != 1 or len(matches) != 2 * count:
                    raise ValueError("Native group/matcher axis differs")
                scene = batch["scan_ids"][0]
                targets = [m.flatten().bool().to(pred["masks"].device) for m in batch["gt_spmasks"]]
                selected = pred["indis"].softmax(-1)[:, :, 1].argmax(-1)
                matched = [sorted(map(int, matches[2 * b + 1][2][0])) for b in range(count)]
                ious = []
                for b in range(count):
                    mask = pred["masks"][b, selected[b], :len(targets[b])] > 0
                    iou = float((mask & targets[b]).sum() / (mask | targets[b]).sum().clamp_min(1))
                    ious.append(iou)
                    outcomes.append({
                        "repeat": repeat, "batch": batch_index, "scene": scene,
                        "ann_id": int(batch["ann_ids"][b]), "frozen": (scene, int(batch["ann_ids"][b])) in frozen,
                        "selected_iou": iou, "batch_input_sha256": fingerprint,
                    })
                for a in range(count):
                    for b in range(a + 1, count):
                        record = {"repeat": repeat, "batch": batch_index, "scene": scene,
                                  "ann_ids": [int(batch["ann_ids"][a]), int(batch["ann_ids"][b])],
                                  "object_ids": [batch["object_idss"][a], batch["object_idss"][b]],
                                  "batch_input_sha256": fingerprint}
                        if set(batch["object_idss"][a]) & set(batch["object_idss"][b]):
                            exclusions.append(dict(record, reason="same_or_overlapping_physical_target"))
                            continue
                        if (targets[a].shape != targets[b].shape
                                or not torch.equal(held["fps"][a], held["fps"][b])
                                or bool((targets[a] & targets[b]).any())):
                            raise ValueError("Distinct target physical support is not aligned")
                        if not matched[a] or not matched[b]:
                            exclusions.append(dict(record, reason="no_native_matched_query"))
                            continue
                        union = targets[a] | targets[b]
                        masks = torch.stack([
                            pred["masks"][k, selected[k], :len(union)] > 0 for k in (a, b)])
                        zs = torch.stack([
                            pred["masks"][k, matched[k][0], :len(union)] for k in (a, b)])
                        record.update({
                            "selected_ious": [ious[a], ious[b]], "either_failed": min(ious[a], ious[b]) <= .5,
                            "target_union_superpoints": int(union.sum()),
                            "selected_overlap": int((masks[0] & masks[1]).sum()),
                            "selected_overlap_on_target": int((masks[0] & masks[1] & union).sum()),
                            "matched_queries": [matched[a][0], matched[b][0]],
                            "matched_overlap_on_target": int(((zs[0] > 0) & (zs[1] > 0) & union).sum()),
                            "probe": pair_probe(torch, zs, torch.stack((targets[a], targets[b]))),
                        })
                        rows.append(record)
                print(json.dumps({"repeat": repeat, "batch": batch_index,
                                  "pairs_so_far": len(rows)}), flush=True)
    finally:
        handle.remove()
        model.criterion.match_sampled_ins = original
    for repeat in range(2):
        if sum(r["repeat"] == repeat and r["frozen"] for r in outcomes) != 31:
            raise ValueError("Frozen expression coverage differs")
    payload = {
        "contract": "m95_distinct_referent_ownership_v1", "admission": False,
        "script_sha256": sha(Path(__file__)), "checkpoint_sha256": sha(args.checkpoint),
        "manifest_sha256": sha(args.manifest), "loader_batches": len(indices),
        "rows": rows, "exclusions": exclusions, "outcomes": outcomes,
        "elapsed_seconds": time.time() - started,
        "peak_allocated_mib": torch.cuda.max_memory_allocated() / (1024 ** 2),
        "training_started": False,
    }
    with output.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(output), "sha256": sha(output), "pairs": len(rows)}))


if __name__ == "__main__":
    main()
