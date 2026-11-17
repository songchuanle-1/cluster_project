"""Frozen native M95 predicted-mask geometry; no model or training mutation."""
import argparse
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys
from collections import defaultdict

from capture_support_20260916 import plain
from frozen_capture_contract_20260916 import file_sha256, model_package_sha256
from native_frozen_capture_20260916 import FrozenDataset

LOWER_SHA = "ecf6d9fe21f254e512b4fc490bc8a843a256a0a8c9e8ae5cab79c86bbf894edc"
UPPER_SHA = "e86746aac35cae5e3a47e6cf277bdc67fbd4dc14efb4ddc9811f68d499bbbe85"
GRAPH_SHA = "4cd1e5e9e3739fbaa892c91c9fd786a292a72d68b381d4898e14470fbd9c1031"
SOURCE_SHA = "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
CHECKPOINT_SHA = "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"


def frozen_rows(lower, upper, graph):
    import re

    bindings = {(r["cohort"], r["scene"], int(r["ann_id"]), str(r["target"])): r
                for r in graph["rows"]}
    if len(bindings) != len(graph["rows"]):
        raise ValueError("Duplicate graph binding")
    selected = {}
    for cohort, doc in (("lower", lower), ("upper", upper)):
        for row in doc["rows"]:
            key = cohort, row["scene"], int(row["ann_id"]), str(row["target"])
            binding = bindings[key]
            cue = {"bottom", "lower"} if cohort == "lower" else {"top", "upper"}
            if not row["same_name_peer_count"] or not any(
                n["node_id"] == 0 and set(re.findall(
                    r"[a-z]+", str(n.get("mod_text", "")).lower())) & cue
                for n in binding["nodes"]
            ):
                continue
            unit = cohort, row["scene"], str(row["target"])
            if unit not in selected or int(row["ann_id"]) < selected[unit]["ann_id"]:
                selected[unit] = {
                    "cohort": cohort, "scene": row["scene"],
                    "ann_id": int(row["ann_id"]), "target": str(row["target"]),
                    "description": row["description"],
                }
    return sorted(selected.values(), key=lambda r: (
        r["cohort"], r["scene"], int(r["target"]), r["ann_id"]))


def pair_geometry(masks, xyz):
    """Build true and rotated peer assignments without scores or ground truth."""
    import numpy as np

    m = np.asarray(masks, dtype=bool)
    points = np.asarray(xyz, dtype=float)
    if m.ndim != 2 or points.shape != (m.shape[1], 3):
        raise ValueError("Mask/XYZ support differs")
    if not np.isfinite(points).all():
        raise ValueError("Nonfinite XYZ")
    eligible = [i for i in range(len(m)) if m[i].any()]
    centers = {i: points[m[i]].mean(axis=0) for i in eligible}
    true, shuffled = {}, {}
    for i in eligible:
        peers = []
        for j in eligible:
            if i == j:
                continue
            overlap = np.logical_and(m[i], m[j]).sum()
            union = np.logical_or(m[i], m[j]).sum()
            if overlap * 2 >= union:
                continue
            delta = centers[i] - centers[j]
            peers.append((float(delta[0] ** 2 + delta[1] ** 2), j))
        if peers:
            true[i] = min(peers)[1]
            ids = sorted(j for _, j in peers)
            shuffled[i] = ids[(ids.index(true[i]) + 1) % len(ids)]
    return {"true": true, "shuffled": shuffled,
            "centers": {i: centers[i].tolist() for i in eligible}}


def main():
    p = argparse.ArgumentParser()
    for name in ("root", "checkpoint", "lower", "upper", "graph", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--validate-only", action="store_true")
    a = p.parse_args()
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "7":
        raise ValueError("Only authorized GPU7")
    root = a.root.resolve()
    out = a.output.resolve()
    if out.exists() or not out.is_relative_to(root.parent / "pipeline"):
        raise ValueError("Output must be new and project-local")
    for path, expected in ((a.lower, LOWER_SHA), (a.upper, UPPER_SHA),
                           (a.graph, GRAPH_SHA)):
        if file_sha256(path) != expected:
            raise ValueError("Frozen cohort hash differs")
    rows = frozen_rows(*(json.loads(p.read_text(encoding="utf-8"))
                         for p in (a.lower, a.upper, a.graph)))
    keys = {(r["scene"], r["ann_id"]): r for r in rows}
    if len(keys) != len(rows):
        raise ValueError("Duplicate expression across units")

    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import torch
    import gorilla
    from framework.dataset import build_dataset, build_dataloader
    from native_manifest_capture_20260922 import ManifestSubset
    torch.set_num_threads(1)
    if not a.validate_only:
        torch.cuda.set_per_process_memory_fraction(0.15)
    config = root / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")
    checkpoint_sha = file_sha256(a.checkpoint)
    if checkpoint_sha != CHECKPOINT_SHA:
        raise ValueError("Champion checkpoint differs")
    cfg_data_root = "/data3/songcl/data/data_cluster/"
    if file_sha256(Path(cfg_data_root) /
                   "scanrefer/ScanRefer_train_new.json") != SOURCE_SHA:
        raise ValueError("Native TRAIN source differs")
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = cfg_data_root
    gorilla.set_random_seed(1999)
    FrozenDataset.checkpoint_sha256 = checkpoint_sha
    source = build_dataset(cfg.data.train, logging.getLogger("group_native"))
    indices = {}
    by_scene_name = defaultdict(set)
    for i, annotations in enumerate(source.scene_inputs):
        for annotation in annotations:
            by_scene_name[(
                annotation["scene_id"],
                " ".join(annotation["object_name"].lower().split()),
            )].add(int(annotation["object_id"]))
            key = annotation["scene_id"], int(annotation["ann_id"])
            if key in keys:
                if str(annotation["object_id"]) != keys[key]["target"]:
                    raise ValueError("Native target identity differs")
                if annotation["description"] != keys[key]["description"]:
                    raise ValueError("Native description differs")
                if key in indices:
                    raise ValueError("Duplicate native expression")
                indices[key] = i
    if set(indices) != set(keys):
        raise ValueError("Missing native TRAIN expressions")
    names = {}
    for key, row in keys.items():
        source_row = next(
            annotation for annotation in source.scene_inputs[indices[key]]
            if annotation["scene_id"] == key[0]
            and int(annotation["ann_id"]) == key[1]
        )
        name_key = key[0], " ".join(source_row["object_name"].lower().split())
        peers = sorted(by_scene_name[name_key] - {int(row["target"])})
        if not peers:
            raise ValueError("Frozen target lacks same-name physical peer")
        names[key] = peers
    if a.validate_only:
        out.mkdir(parents=True)
        (out / "validation.json").write_text(json.dumps({
            "contract": "m95_group_predicted_peer_validation_v1",
            "admission": False, "train_source_sha256": SOURCE_SHA,
            "checkpoint_sha256": checkpoint_sha,
            "config_sha256": file_sha256(config),
            "frozen_rows": len(rows), "native_expression_ids": len(indices),
            "native_scene_batches": len(set(indices.values())),
            "gpu_execution": False,
        }, sort_keys=True, indent=2) + "\n", encoding="ascii")
        return
    adapter = FrozenDataset(source, out.name, file_sha256(Path(__file__)))
    dataset = ManifestSubset(adapter, sorted(set(indices.values())))
    loader = build_dataloader(dataset, batch_size=2, num_workers=0,
                              persistent_workers=False)
    model = importlib.import_module(
        "framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(a.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    held = {}

    def criterion(module, inputs):
        held.update(pred=inputs[0], gt=inputs[1], labels=inputs[4],
                    pos=inputs[8], offsets=inputs[9])

    hook = model.criterion.register_forward_pre_hook(criterion)
    results = {}
    out.mkdir(parents=True)
    try:
        with torch.no_grad():
            for step, (batch, axes) in enumerate(loader):
                held.clear()
                gorilla.set_random_seed(1999)
                loss, _ = model(batch, mode="loss")
                if not bool(torch.isfinite(loss).all()):
                    raise ValueError("Nonfinite native loss")
                pred = held["pred"]
                for b, axis in enumerate(axes):
                    key = axis["scene"], int(axis["ann_id"])
                    if key not in keys:
                        continue
                    if key in results:
                        raise ValueError("Duplicate captured expression")
                    n = len(axis["original_superpoint_ids"])
                    offsets = held["offsets"]
                    xyz = held["pos"][int(offsets[b]):int(offsets[b + 1])]
                    if xyz.shape != (n, 3):
                        raise ValueError("Position support differs")
                    if int((~pred["batch_mask"][b]).sum()) != n:
                        raise ValueError("Native valid mask differs")
                    if int(pred["masks"].shape[1]) != 128:
                        raise ValueError("Expected 128 native proposals")
                    masks = (pred["masks"][b, :, :n] > 0).cpu().numpy()
                    geometry = pair_geometry(masks, xyz.cpu().numpy())
                    target = held["gt"][b].reshape(-1).bool()
                    if len(target) != n or len(held["labels"][b]) != n:
                        raise ValueError("Native GT support differs")
                    results[key] = {
                        **keys[key], "axis": axis, "step": step,
                        "masks": masks.tolist(), "xyz": xyz.cpu().tolist(),
                        "centers": geometry["centers"],
                        "true_peer": geometry["true"],
                        "shuffled_peer": geometry["shuffled"],
                        "target_mask": target.cpu().tolist(),
                        "physical_labels": plain(held["labels"][b].cpu()),
                        "same_name_peer_ids": names[key],
                        "scores": pred["indis"][b].softmax(-1)[:, 1].cpu().tolist(),
                    }
                print(json.dumps({"step": step, "found": len(results)}), flush=True)
        if set(results) != set(keys):
            raise ValueError("Incomplete native expression capture")
        document = {
            "contract": "m95_group_predicted_peer_v1", "admission": False,
            "checkpoint_sha256": checkpoint_sha,
            "config_sha256": file_sha256(config),
            "model_source_sha256": model_package_sha256(root, NAME),
            "producer_sha256": file_sha256(Path(__file__)),
            "cohort_sha256": [LOWER_SHA, UPPER_SHA, GRAPH_SHA],
            "rows": [results[k] for k in sorted(results)],
        }
        (out / "capture.json").write_text(
            json.dumps(document, sort_keys=True) + "\n", encoding="ascii")
    finally:
        hook.remove()


if __name__ == "__main__":
    main()
