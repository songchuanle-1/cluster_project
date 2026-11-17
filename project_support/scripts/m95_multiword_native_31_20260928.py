"""Native M95 outcome capture for a frozen two-scene TRAIN cohort.

Run only with an independently acquired exclusive GPU7 diagnostic lease.
This script does not alter model, dataset, loss or checkpoint files.
"""
import argparse
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys


NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
MANIFEST_SHA = "85e108e8c86d65bcdbdc25061987e0a973fa45b35b00030d0721d359da720040"
CHECKPOINT_SHA = "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
DATASET_SHA = "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
ANNOTATION_SHA = "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
GRAPH_SHA = "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def frozen_rows(path):
    if sha(path) != MANIFEST_SHA:
        raise ValueError("Frozen manifest hash differs")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["contract"] != "m95_multiword_capture_manifest_v1":
        raise ValueError("Manifest contract differs")
    rows = {(row["scene"], int(row["ann_id"])): row for row in data["records"]}
    if (len(rows) != 31 or len(data["records"]) != 31
            or len({scene for scene, _ in rows}) != 2
            or sum(row["arm"] == "phrase" for row in rows.values()) != 11):
        raise ValueError("Frozen cohort differs")
    return rows


def select_native_indices(dataset, rows):
    """Verify original utterance and physical target before any model forward."""
    selected, found = [], set()
    for index, group in enumerate(dataset.scene_inputs):
        matches = []
        for item in group:
            key = item["scene_id"], int(item["ann_id"])
            if key not in rows:
                continue
            if key in found:
                raise ValueError("Duplicate native annotation")
            frozen = rows[key]
            text = (" ".join(dataset.scene_graphs[key[0]][str(key[1])]["utterance"]
                             .replace(",", " ,").split()) + " . not mentioned")
            target = item.get("object_ids", [item.get("object_id")])
            if text != frozen["text"] or sorted(map(int, target)) != sorted(
                    map(int, frozen["target_instances"])):
                raise ValueError("Original text or target differs: %s" % (key,))
            found.add(key)
            matches.append(key)
        if matches:
            selected.append(index)
    if set(rows) != found:
        raise ValueError("Native dataset lacks %d frozen expressions" % len(set(rows) - found))
    return selected


def selected_loader(source, indices, data_loader_cls):
    class Selected:
        def __len__(self):
            return len(indices)

        def __getitem__(self, index):
            return source[indices[index]]

        def collate_fn(self, items):
            return source.collate_fn(items)

    selected = Selected()
    return data_loader_cls(selected, batch_size=1, num_workers=0,
                           shuffle=False, drop_last=False, pin_memory=True,
                           collate_fn=selected.collate_fn)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    if (os.environ.get("CUDA_VISIBLE_DEVICES") != "7" or output.exists()
            or not output.is_relative_to(root.parent / "pipeline")
            or sha(args.checkpoint) != CHECKPOINT_SHA):
        raise ValueError("GPU7, fresh project output and frozen checkpoint required")
    frozen = frozen_rows(args.manifest)
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import torch
    import gorilla
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader
    from m95_final_seed_target_probe_20260927 import batch_fingerprint

    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    config = root / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")
    cfg = gorilla.Config.fromfile(str(config))
    data_root = Path("/data3/songcl/data/data_cluster/")
    inputs = {
        "dataset": root / "framework/dataset/scannetv2.py",
        "annotations": data_root / "scanrefer/ScanRefer_train_new.json",
        "graphs": data_root / "scanrefer/scene_graphs_new_train.json",
    }
    expected = {"dataset": DATASET_SHA, "annotations": ANNOTATION_SHA,
                "graphs": GRAPH_SHA}
    if {name: sha(path) for name, path in inputs.items()} != expected:
        raise ValueError("Frozen native source hashes differ")
    cfg.model.data_root = cfg.data.train.data_root = str(data_root) + "/"
    gorilla.set_random_seed(1999)
    source = build_dataset(cfg.data.train, logging.getLogger("m95_multiword_31"))
    indices = select_native_indices(source, frozen)

    loader = selected_loader(source, indices, DataLoader)
    model = importlib.import_module(
        "framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    held = {}
    handle = model.criterion.register_forward_pre_hook(
        lambda module, inputs: held.update(pred=inputs[0], fps=inputs[7],
                                           labels=inputs[4]))
    results = []
    try:
        with torch.no_grad():
            for step, batch in enumerate(loader):
                fingerprint = batch_fingerprint(torch, batch)
                held.clear()
                gorilla.set_random_seed(1999)
                loss, _ = model(batch, mode="loss")
                if not bool(torch.isfinite(loss).all()):
                    raise ValueError("Nonfinite native loss")
                pred = held["pred"]
                scenes = [scene for scene, count in zip(
                    batch["scan_ids"], batch["scenes_len"])
                    for _ in range(int(count))]
                if len(scenes) != len(batch["ann_ids"]):
                    raise ValueError("Native annotation axis differs")
                for b, (scene, aid) in enumerate(zip(scenes, batch["ann_ids"])):
                    key = scene, int(aid)
                    if key not in frozen:
                        continue
                    frozen_target = sorted(map(int, frozen[key]["target_instances"]))
                    if sorted(map(int, batch["object_idss"][b])) != frozen_target:
                        raise ValueError("Native target changed")
                    target = batch["gt_spmasks"][b].to(pred["masks"].device).flatten().bool()
                    if not bool(target.any()):
                        raise ValueError("Empty native superpoint target")
                    scores = pred["indis"][b].softmax(-1)[:, 1]
                    selected = int(scores.argmax())
                    mask = pred["masks"][b, selected, :len(target)] > 0
                    iou = float((mask & target).sum().float()
                                / (mask | target).sum().clamp_min(1))
                    seed_index = int(pred["sample_inds"][b, selected])
                    seed_superpoint = int(held["fps"][b, seed_index])
                    label = int(held["labels"][b][seed_superpoint])
                    results.append({
                        "scene": scene, "ann_id": int(aid), "arm": frozen[key]["arm"],
                        "target_instances": frozen_target,
                        "batch": step, "batch_input_sha256": fingerprint,
                        "selected_query": selected, "selected_mask_iou": iou,
                        "selected_seed_superpoint": seed_superpoint,
                        "selected_seed_majority_instance": label,
                        "seed_majority_matches_target": label in frozen_target,
                    })
    finally:
        handle.remove()
    if len(results) != len(frozen) or {
            (row["scene"], row["ann_id"]) for row in results} != set(frozen):
        raise ValueError("Incomplete native cohort")
    result = {
        "contract": "m95_multiword_native_31_v1", "admission": False,
        "manifest_sha256": MANIFEST_SHA, "checkpoint_sha256": CHECKPOINT_SHA,
        "config_sha256": sha(config), "inputs": expected, "seed": 1999,
        "rows": results,
        "limits": "TRAIN descriptions differ, two scenes only; no same-input intervention, backward or efficacy claim.",
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"rows": len(results), "scenes": len({r["scene"] for r in results})}))


if __name__ == "__main__":
    main()
