"""Compare the original-order row83 sparse boundary to a same-process replay."""
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
from m95_matched_sparse_context_20260926 import compare_tensors
from frozen_capture_contract_20260916 import model_package_sha256
from native_manifest_capture_20260922 import load_manifest


BATCH_SHA256 = "ed835ab21f071048e1d1cdd8fb19b6dd4ac24770b65e85ee4048931edb3d0529"
FULL_ORDER_SHA256 = "0de128c44bb103ad2e3b7690e27e83b5d2f310c1e59b0087f9ddf2457dbbd742"


def compare_snapshots(original, replay):
    stages = {}
    for key in ("input", "input_indices", "first", "first_indices",
                "sparse", "sparse_indices"):
        stages[key] = {
            "original_sha256": digest(original[key]),
            "replay_sha256": digest(replay[key]),
            "delta": compare_tensors(original[key], replay[key]),
        }
    return stages


def main():
    parser = argparse.ArgumentParser()
    for name in ("root", "bundle", "checkpoint", "manifest", "batch",
                 "full-order", "output", "progress"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "7":
        raise ValueError("Authorized physical GPU7 required")
    output, progress = Path(args.output), Path(args.progress)
    if output.exists() or progress.exists() or output == progress:
        raise ValueError("Output/progress already exists")
    root = Path(args.root).resolve()
    sys.path[:0] = [str(Path(args.bundle).resolve()), str(Path(__file__).resolve().parent),
                    str(root), str(root / "framework/lib")]
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    import gorilla
    import torch
    from framework.dataset import build_dataset, build_dataloader

    config = root / "configs/Quard/ctf_hcg_csort" / (MODEL_NAME + ".yaml")
    bindings = ((config, CONFIG_SHA256), (args.checkpoint, CHECKPOINT_SHA256),
                (args.manifest, MANIFEST_SHA256), (args.batch, BATCH_SHA256),
                (args.full_order, FULL_ORDER_SHA256))
    if any(sha256(path) != expected for path, expected in bindings):
        raise ValueError("Frozen input identity differs")
    if model_package_sha256(root, MODEL_NAME) != MODEL_SHA256:
        raise ValueError("Frozen model source differs")
    previous = json.loads(Path(args.full_order).read_text(encoding="ascii"))
    if (previous["contract"] != "m95_full_producer_boundary_v1"
            or previous["native_item_sha256"] != EXPECTED[83][2]):
        raise ValueError("Original-order receipt differs")
    saved = torch.load(args.batch, map_location="cpu", weights_only=False)
    step_expected, index_expected, item_expected = EXPECTED[83]
    if (saved["step"], saved["dataset_index"], saved["native_item_sha256"]) != (
            step_expected, index_expected, item_expected):
        raise ValueError("Frozen batch target differs")
    manifest = load_manifest(args.manifest, MANIFEST_SHA256)
    row = next(v for v in manifest.rows.values() if v["manifest_index"] == 83)

    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    gorilla.set_random_seed(1999)
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    dataset = build_dataset(cfg.data.train, logging.getLogger("full_order_first_stage"))
    subset = HashedDataset(dataset, {index_expected})
    loader = build_dataloader(subset, batch_size=2, num_workers=0,
                              persistent_workers=False)
    model = importlib.import_module(
        "framework.model.Quard_model." + MODEL_NAME).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    del state
    model.cuda().eval()
    held = {}

    def capture(name):
        def hook(module, inputs, result=None):
            if not held.get("capture"):
                return
            tensor = inputs[0] if result is None else result
            held[name] = tensor.features.detach().cpu().clone()
            held[name + "_indices"] = tensor.indices.detach().cpu().clone()
        return hook

    hooks = [
        model.input_conv.register_forward_pre_hook(capture("input")),
        model.input_conv.register_forward_hook(capture("first")),
        model.output_layer.register_forward_hook(capture("sparse")),
        model.criterion.register_forward_pre_hook(
            lambda module, inputs: held.update(pred=inputs[0], gt=inputs[1],
                                                offsets=inputs[9])
            if held.get("capture") else None),
    ]

    def readout(batch):
        scene = [str(x) for x in batch["scan_ids"]].index(row["scene_id"])
        lengths = [int(x) for x in batch["scenes_len"]]
        slots = [i for i in range(sum(lengths[:scene]), sum(lengths[:scene + 1]))
                 if int(batch["ann_ids"][i]) == row["ann_id"]]
        if len(slots) != 1:
            raise ValueError("Expression slot differs")
        slot = slots[0]
        n = int(held["offsets"][slot + 1] - held["offsets"][slot])
        pred = held["pred"]
        scores = pred["indis"][slot].softmax(-1)[:, 1]
        selected = int(scores.argmax())
        target = held["gt"][slot].reshape(-1).bool()
        mask = pred["masks"][slot, selected, :n] > 0
        return {
            "expression_slot": slot, "selected_query": selected,
            "selected_iou": float((mask & target).sum().float()
                                  / (mask | target).sum().clamp_min(1)),
            "point169_logit": float(pred["masks"][slot, 103, 169]),
            "p2v_map_sha256": digest(batch["p2v_map"]),
            "superpoints_sha256": digest(batch["superpoints"]),
        }

    record_progress(progress, {"event": "started", "target_step": step_expected,
                               "dataset_size": len(dataset)})
    try:
        with torch.no_grad():
            for step, batch in enumerate(loader):
                if step > step_expected:
                    break
                if len(subset.pending) != 2:
                    raise ValueError("Loader item count differs")
                held.clear()
                held["capture"] = step == step_expected
                if held["capture"]:
                    found = [fingerprint for index, fingerprint in subset.pending
                             if index == index_expected]
                    if found != [item_expected] or batch["scan_ids"] != saved["batch"]["scan_ids"]:
                        raise ValueError("Original-order row83 identity differs")
                subset.pending.clear()
                gorilla.set_random_seed(1999)
                loss, _ = model(batch, mode="loss")
                if not bool(torch.isfinite(loss)):
                    raise ValueError("Nonfinite original-order loss")
                if step % 100 == 0:
                    record_progress(progress, {"event": "progress", "step": step})
                if not held["capture"]:
                    continue
                keys = ("input", "input_indices", "first", "first_indices",
                        "sparse", "sparse_indices")
                original = {key: held[key] for key in keys}
                original_readout = readout(batch)
                if digest(original["sparse"]) != previous["sparse_output_sha256"]:
                    record_progress(progress, {"event": "original_sparse_hash_drift",
                                               "step": step})
                held.clear()
                held["capture"] = True
                gorilla.set_random_seed(1999)
                loss, _ = model(saved["batch"], mode="loss")
                if not bool(torch.isfinite(loss)):
                    raise ValueError("Nonfinite frozen-batch loss")
                replay = {key: held[key] for key in keys}
                replay_readout = readout(saved["batch"])
                result = {
                    "contract": "m95_full_order_first_stage_v1",
                    "step": step, "dataset_index": index_expected,
                    "native_item_sha256": item_expected,
                    "identities": {str(path): expected for path, expected in bindings},
                    "model_source_sha256": MODEL_SHA256,
                    "comparison": compare_snapshots(original, replay),
                    "original": original_readout, "replay": replay_readout,
                    "strict_comparator": "unchanged_fail_26_of_65",
                    "historical_reference_upstream": "unavailable",
                    "admission": False,
                }
                output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                                  encoding="ascii")
                record_progress(progress, {"event": "complete", "step": step,
                                           "output_sha256": sha256(output)})
                break
    finally:
        for hook in hooks:
            hook.remove()
    if not output.exists():
        raise ValueError("Original-order row83 was not reached")


if __name__ == "__main__":
    main()
