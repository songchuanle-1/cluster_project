"""Capture the M95 row-83 boundary in original full-TRAIN producer order."""
import argparse
import importlib
import json
import logging
import os
from pathlib import Path
import sys

from m95_frozen_item_replay_20260926 import (
    CHECKPOINT_SHA256, CONFIG_SHA256, EXPECTED, HashedDataset,
    MANIFEST_SHA256, MODEL_SHA256, record_progress, sha256,
)
from m95_frozen_batch_cluster_control_20260926 import MODEL_NAME, digest
from frozen_capture_contract_20260916 import model_package_sha256
from native_manifest_capture_20260922 import load_manifest


def main():
    parser = argparse.ArgumentParser()
    for name in ("root", "checkpoint", "manifest", "batch", "reference",
                 "strict", "saved-trace", "output", "progress"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "7":
        raise ValueError("Authorized physical GPU7 required")
    output, progress = Path(args.output), Path(args.progress)
    if output.exists() or progress.exists() or output == progress:
        raise ValueError("Output/progress already exists")
    root = Path(args.root).resolve()
    sys.path[:0] = [str(Path(__file__).resolve().parent), str(root),
                    str(root / "framework/lib")]
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    import gorilla
    import torch
    from torch_scatter import scatter_mean
    from framework.dataset import build_dataset, build_dataloader

    config = root / "configs/Quard/ctf_hcg_csort" / (MODEL_NAME + ".yaml")
    if (sha256(config) != CONFIG_SHA256
            or sha256(args.checkpoint) != CHECKPOINT_SHA256
            or model_package_sha256(root, MODEL_NAME) != MODEL_SHA256):
        raise ValueError("Model/checkpoint identity differs")
    if sha256(args.batch) != "ed835ab21f071048e1d1cdd8fb19b6dd4ac24770b65e85ee4048931edb3d0529":
        raise ValueError("Saved batch identity differs")
    manifest = load_manifest(args.manifest, MANIFEST_SHA256)
    row = next(value for value in manifest.rows.values()
               if value["manifest_index"] == 83)
    saved = torch.load(args.batch, map_location="cpu", weights_only=False)
    expected_step, expected_index, expected_item = EXPECTED[83]
    if (saved["step"] != expected_step or saved["dataset_index"] != expected_index
            or saved["native_item_sha256"] != expected_item):
        raise ValueError("Saved target identity differs")
    artifacts = {}
    for tag, path, expected_hash in (
        ("reference", args.reference, "5c14212dfdd7bbf9ab39c5dc1fc02555dfbbcd219e672271e6097e1ddd0f5844"),
        ("strict", args.strict, "7afb7a40342c746f5600029b087190169fec8da79bbd3192a3cab01f707bb5ce"),
    ):
        if sha256(path) != expected_hash:
            raise ValueError(tag + " artifact identity differs")
        entries = torch.load(path, map_location="cpu", weights_only=False)
        match = [value for value in entries if value["manifest_index"] == 83]
        if len(match) != 1 or match[0]["axis"]["native_input_sha256"] != expected_item:
            raise ValueError(tag + " artifact row differs")
        artifacts[tag] = match[0]
    previous = json.loads(Path(args.saved_trace).read_text(encoding="ascii"))
    if (previous["contract"] != "m95_superpoint_reduction_trace_v1"
            or previous["batch_sha256"] != sha256(args.batch)
            or previous["checkpoint_sha256"] != CHECKPOINT_SHA256):
        raise ValueError("Saved-batch trace binding differs")

    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    gorilla.set_random_seed(1999)
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    dataset = build_dataset(cfg.data.train, logging.getLogger("full_producer_boundary"))
    subset = HashedDataset(dataset, {expected_index})
    loader = build_dataloader(subset, batch_size=2, num_workers=0,
                              persistent_workers=False)
    model = importlib.import_module(
        "framework.model.Quard_model." + MODEL_NAME
    ).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    del state
    model.cuda().eval()
    network = importlib.import_module(
        "framework.model.Quard_model." + MODEL_NAME + ".network"
    )
    if network.scatter_mean is not scatter_mean or model.pool != "mean":
        raise ValueError("Unexpected native reduction binding")
    held = {}
    hooks = [
        model.output_layer.register_forward_hook(
            lambda module, inputs, result: held.update(
                sparse_output=result.features.detach().clone())
            if held.get("capture") else None),
        model.dec.input_proj.register_forward_pre_hook(
            lambda module, inputs: held.update(raw_3d=inputs[0].detach().clone())
            if held.get("capture") else None),
        model.criterion.register_forward_pre_hook(
            lambda module, inputs: held.update(pred=inputs[0], gt=inputs[1],
                                                offsets=inputs[9])
            if held.get("capture") else None),
    ]
    record_progress(progress, {"event": "started", "target_step": expected_step,
                               "dataset_size": len(dataset)})
    try:
        with torch.no_grad():
            for step, batch in enumerate(loader):
                if step > expected_step:
                    break
                if len(subset.pending) != 2:
                    raise ValueError("Loader item count differs")
                held.clear()
                held["capture"] = step == expected_step
                if held["capture"]:
                    found = [digest_value for index, digest_value in subset.pending
                             if index == expected_index]
                    if found != [expected_item]:
                        raise ValueError("Native row-83 item fingerprint differs")
                    if batch["scan_ids"] != saved["batch"]["scan_ids"]:
                        raise ValueError("Scene batch order differs")

                    def traced_scatter(source, index, *pos, **kwargs):
                        value = scatter_mean(source, index, *pos, **kwargs)
                        held.setdefault("scatter_calls", []).append({
                            "source_sha256": digest(source),
                            "index_sha256": digest(index),
                            "output_sha256": digest(value),
                            "source_shape": list(source.shape),
                            "output_shape": list(value.shape),
                        })
                        return value

                    network.scatter_mean = traced_scatter
                subset.pending.clear()
                gorilla.set_random_seed(1999)
                loss, _ = model(batch, mode="loss")
                if not bool(torch.isfinite(loss)):
                    raise ValueError("Nonfinite native loss")
                if step % 100 == 0:
                    record_progress(progress, {"event": "progress", "step": step})
                if not held["capture"]:
                    continue
                scene_index = [str(x) for x in batch["scan_ids"]].index(row["scene_id"])
                lengths = [int(x) for x in batch["scenes_len"]]
                slots = [i for i in range(sum(lengths[:scene_index]),
                                          sum(lengths[:scene_index + 1]))
                         if int(batch["ann_ids"][i]) == row["ann_id"]]
                if len(slots) != 1 or len(held.get("scatter_calls", [])) < 2:
                    raise ValueError("Missing expression/reduction axis")
                slot = slots[0]
                offsets = held["offsets"]
                n = int(offsets[slot + 1] - offsets[slot])
                feature = model.dec.get_batches(held["raw_3d"], offsets)[0][slot, :n].cpu()
                pred = held["pred"]
                query = 103
                logits = pred["masks"][slot, query, :n].detach().cpu()
                scores = pred["indis"][slot].softmax(-1)[:, 1]
                selected = int(scores.argmax())
                target = held["gt"][slot].reshape(-1).bool().cpu()
                mask = pred["masks"][slot, selected, :n].detach().cpu() > 0
                comparisons = {}
                for tag, artifact in artifacts.items():
                    frozen = artifact["features"]["raw_3d"]
                    if feature.shape != frozen.shape or not torch.equal(
                            artifact["target_union"].bool(), target):
                        raise ValueError(tag + " support differs")
                    comparisons[tag] = {
                        "raw_3d_max_abs": float((feature - frozen).abs().max()),
                        "raw_3d_sha256": digest(frozen),
                        "probe_changed_points": int(((logits > 0) !=
                            (artifact["query_mask_logits"][query] > 0)).sum()),
                        "point169_logit": float(artifact["query_mask_logits"][query, 169]),
                    }
                result = {
                    "contract": "m95_full_producer_boundary_v1",
                    "step": step, "dataset_index": expected_index,
                    "manifest_index": 83, "expression_slot": slot,
                    "native_item_sha256": expected_item,
                    "checkpoint_sha256": CHECKPOINT_SHA256,
                    "config_sha256": CONFIG_SHA256,
                    "model_source_sha256": MODEL_SHA256,
                    "saved_batch_sha256": sha256(args.batch),
                    "saved_trace_sha256": sha256(args.saved_trace),
                    "artifact_sha256": {tag: sha256(path) for tag, path in
                        (("reference", args.reference), ("strict", args.strict))},
                    "sparse_output_sha256": digest(held["sparse_output"]),
                    "p2v_map_sha256": digest(batch["p2v_map"]),
                    "superpoints_sha256": digest(batch["superpoints"]),
                    "scatter_calls": held["scatter_calls"],
                    "raw_3d_sha256": digest(feature),
                    "point169_logit": float(logits[169]),
                    "selected_query": selected,
                    "selected_iou": float((mask & target).sum().float()
                                          / (mask | target).sum().clamp_min(1)),
                    "comparisons": comparisons,
                    "strict_fullscan_comparator": "unchanged_fail_26_of_65",
                    "admission": False,
                }
                output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                                  encoding="ascii")
                record_progress(progress, {"event": "complete", "step": step,
                                           "output_sha256": sha256(output)})
                break
    finally:
        network.scatter_mean = scatter_mean
        for hook in hooks:
            hook.remove()
    if not output.exists():
        raise ValueError("Row-83 full producer was not reached")


if __name__ == "__main__":
    main()
