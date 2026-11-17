"""Frozen native point-detail diagnosis, without optimization or repartition."""
import argparse
import hashlib
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


def main():
    parser = argparse.ArgumentParser()
    for name in ("root", "checkpoint", "manifest", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if (os.name != "posix" or os.environ.get("CUDA_VISIBLE_DEVICES") != "7"
            or args.output.exists()
            or not args.output.resolve().is_relative_to(root.parent / "pipeline")
            or sha(args.checkpoint) != CHECKPOINT_SHA):
        raise ValueError("Fresh project output, frozen checkpoint and GPU7 required")
    data_root = Path("/data3/songcl/data/data_cluster")
    frozen = frozen_rows(args.manifest)
    sources = {
        "dataset": root / "framework/dataset/scannetv2.py",
        "annotations": data_root / "scanrefer/ScanRefer_train_new.json",
        "graphs": data_root / "scanrefer/scene_graphs_new_train.json",
        "network": root / "framework/model/Quard_model" / NAME / "network.py",
    }
    expected = {
        "dataset": DATASET_SHA, "annotations": ANNOTATION_SHA, "graphs": GRAPH_SHA,
        "network": "5a77eb852b3c6e5de2804d80a2c7a16504f1fd8a57aa94dc6045d9f35587625d",
    }
    if {k: sha(p) for k, p in sources.items()} != expected:
        raise ValueError("Frozen native inputs changed")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import torch
    import gorilla
    from torch_scatter import scatter_mean, scatter_sum
    from torch.utils.data import DataLoader
    from framework.dataset import build_dataset
    from m95_final_seed_target_probe_20260927 import batch_fingerprint

    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.20)
    cfg = gorilla.Config.fromfile(str(
        root / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")))
    cfg.model.data_root = cfg.data.train.data_root = str(data_root) + "/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("point-detail"))
    population = os.environ.get("POINT_DETAIL_POPULATION") == "1"
    if population:
        first = {}
        excluded = {scene for scene, _ in frozen}
        for index, group in enumerate(dataset.scene_inputs):
            scene = group[0]["scene_id"]
            if scene not in excluded:
                first.setdefault(scene, index)
        scenes = sorted(first, key=lambda s: hashlib.sha256(
            ("point-detail-20261009:" + s).encode()).hexdigest())[:32]
        indices = [first[s] for s in scenes]
        manifest = [{"scene": s, "native_group": first[s],
                     "annotations": [{"ann_id": row["ann_id"],
                                      "object_ids": row.get("object_ids", [row.get("object_id")])}
                                     for row in dataset.scene_inputs[first[s]]]}
                    for s in scenes]
        with args.output.with_suffix(".manifest.json").open("x", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2)
    else:
        indices = select_native_indices(dataset, frozen)
    model = importlib.import_module("framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    held = {}
    hook = model.output_layer.register_forward_hook(
        lambda module, inputs, output: held.update(voxel=output.features.detach()))
    records = []
    started = time.time()
    try:
        for repeat in range(2):
            gorilla.set_random_seed(1999)
            loader = selected_loader(dataset, indices, DataLoader)
            for bi, batch in enumerate(loader):
                fingerprint = batch_fingerprint(torch, batch)
                held.clear()
                gorilla.set_random_seed(1999)
                with torch.no_grad():
                    native_loss, _ = model(batch, mode="loss")
                if not bool(torch.isfinite(native_loss).all()):
                    raise ValueError("Nonfinite native loss")
                device = held["voxel"].device
                point = held["voxel"][batch["p2v_map"].to(device).long()]
                sp = batch["superpoints"].to(device).long()
                detail = point - scatter_mean(point, sp, dim=0)[sp]
                scene_ids = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
                             for _ in range(int(n))]
                row_start = 0
                for si, count in enumerate(batch["scenes_len"]):
                    low, high = [int(v) for v in batch["batch_offsets"][si:si+2]]
                    keep = (sp >= low) & (sp < high)
                    local_sp = sp[keep] - low
                    local_f, local_detail = point[keep], detail[keep]
                    points_per_sp = scatter_sum(torch.ones_like(local_sp), local_sp, dim=0)
                    for ri in range(row_start, row_start + int(count)):
                        target = batch["gt_pmasks"][ri].to(device).flatten().float()
                        if target.numel() != len(local_sp):
                            raise ValueError("Point target binding differs")
                        fraction = scatter_mean(target, local_sp, dim=0)
                        mixed = (fraction > 0) & (fraction < 1)
                        mixed_point = mixed[local_sp]
                        majority = fraction[local_sp] > 0.5
                        energy = local_detail.square().sum(-1)
                        denom = local_f.square().sum(-1).sum().clamp_min(1e-12)
                        centered_target = target - fraction[local_sp]
                        covariance = scatter_sum(
                            local_detail * centered_target[:, None], local_sp, dim=0)
                        # Within-SP cyclic permutation preserves every feature multiset.
                        order = local_sp.argsort(stable=True)
                        group_start = points_per_sp.cumsum(0) - points_per_sp
                        position = torch.arange(len(order), device=device)
                        sorted_sp = local_sp[order]
                        next_pos = group_start[sorted_sp] + (
                            position - group_start[sorted_sp] + 1) % points_per_sp[sorted_sp]
                        permuted = torch.empty_like(local_detail)
                        permuted[order] = local_detail[order[next_pos]]
                        shuffled_cov = scatter_sum(
                            permuted * centered_target[:, None], local_sp, dim=0)
                        record = {
                            "repeat": repeat, "batch": bi, "scene": scene_ids[ri],
                            "ann_id": int(batch["ann_ids"][ri]),
                            "frozen": (scene_ids[ri], int(batch["ann_ids"][ri])) in frozen,
                            "input_sha256": fingerprint, "points": len(local_sp),
                            "superpoints": high - low, "mixed_superpoints": int(mixed.sum()),
                            "mixed_points": int(mixed_point.sum()),
                            "target_points": int(target.sum()),
                            "majority_disagreement_points": int((majority != target.bool()).sum()),
                            "normalized_detail_energy": float(energy.sum() / denom),
                            "normalized_mixed_detail_energy": float(energy[mixed_point].sum() / denom),
                            "broadcast_detail_energy": 0.0,
                            "detail_target_covariance_norm": float(covariance.norm()),
                            "permuted_target_covariance_norm": float(shuffled_cov.norm()),
                            "detail_finite": bool(torch.isfinite(local_detail).all()),
                        }
                        records.append(record)
                    row_start += int(count)
                print(json.dumps({"repeat": repeat, "batch": bi}), flush=True)
                del point, detail, native_loss
    finally:
        hook.remove()
    pairs = {}
    for row in records:
        key = (row["scene"], row["ann_id"])
        pairs.setdefault(key, {})[row["repeat"]] = row
    discrete = ("points", "superpoints", "mixed_superpoints", "mixed_points",
                "target_points", "majority_disagreement_points", "input_sha256")
    normalized = ("normalized_detail_energy", "normalized_mixed_detail_energy")
    drift = max(abs(a[k] - b[k]) for a, b in (v.values() for v in pairs.values())
                for k in normalized)
    agreement = all(a[k] == b[k] for a, b in (v.values() for v in pairs.values())
                    for k in discrete)
    cohort = [r for r in records if r["repeat"] == 0 and (population or r["frozen"])]
    if ((not population and len(cohort) != 31)
            or any(len(p) != 2 for p in pairs.values())):
        raise ValueError("Repeat or frozen cohort incomplete")
    result = {
        "contract": "m95_native_point_detail_v1", "admission": False,
        "population_extension": population,
        "script_sha256": sha(Path(__file__)), "manifest_sha256": sha(args.manifest),
        "checkpoint_sha256": sha(args.checkpoint), "sources": expected,
        "records": records,
        "summary": {
            "frozen_expressions": len(cohort), "all_expressions": len(pairs),
            "scenes": len({r["scene"] for r in cohort}),
            "frozen_with_mixed_sp": sum(r["mixed_superpoints"] > 0 for r in cohort),
            "frozen_with_nonzero_mixed_detail": sum(r["normalized_mixed_detail_energy"] > 0 for r in cohort),
            "max_normalized_repeat_drift": drift,
            "strict_repeat_pass": drift <= 1e-6 and agreement,
            "discrete_input_agreement": agreement,
        },
        "elapsed_seconds": time.time() - started,
        "peak_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
        "optimizer_created": False, "training_started": False,
    }
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result["summary"]), flush=True)


if __name__ == "__main__":
    main()
