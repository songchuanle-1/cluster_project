"""Trace the bound M95 backbone-to-superpoint feature boundary."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys

def main():
    parser = argparse.ArgumentParser()
    for name in ("root", "bundle", "checkpoint", "batch", "manifest",
                 "reference", "strict", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--repeats", type=int, default=4)
    args = parser.parse_args()
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "7" or not 2 <= args.repeats <= 8:
        raise ValueError("Authorized GPU7 and bounded repeats required")
    output = Path(args.output)
    if output.exists():
        raise ValueError("Output exists")
    root = Path(args.root).resolve()
    sys.path[:0] = [str(Path(args.bundle).resolve()),
                    str(Path(__file__).resolve().parent), str(root),
                    str(root / "framework/lib")]
    from m95_frozen_batch_cluster_control_20260926 import (
        CHECKPOINT_SHA256, CONFIG_SHA256, MODEL_NAME, MODEL_SHA256,
        EXPECTED, digest, sha256,
    )
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    import gorilla
    import torch
    from torch_scatter import scatter_mean
    from frozen_capture_contract_20260916 import model_package_sha256
    from native_manifest_capture_20260922 import load_manifest

    config = root / "configs/Quard/ctf_hcg_csort" / (MODEL_NAME + ".yaml")
    if (sha256(config) != CONFIG_SHA256
            or sha256(args.checkpoint) != CHECKPOINT_SHA256
            or model_package_sha256(root, MODEL_NAME) != MODEL_SHA256):
        raise ValueError("Model identity differs")
    expected, query = EXPECTED[83]
    saved = torch.load(args.batch, map_location="cpu", weights_only=False)
    if (saved["contract"] != "m95_frozen_target_batch_v1"
            or saved["manifest_index"] != 83
            or saved["native_item_sha256"] != expected
            or saved["frozen_native_input_sha256"] != expected):
        raise ValueError("Saved item identity differs")
    manifest = load_manifest(args.manifest,
                             "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023")
    row = next(value for value in manifest.rows.values()
               if value["manifest_index"] == 83)
    batch = saved["batch"]
    scene_index = [str(x) for x in batch["scan_ids"]].index(row["scene_id"])
    lengths = [int(x) for x in batch["scenes_len"]]
    slots = [i for i in range(sum(lengths[:scene_index]),
                               sum(lengths[:scene_index + 1]))
             if int(batch["ann_ids"][i]) == row["ann_id"]]
    if len(slots) != 1:
        raise ValueError("Expression slot differs")
    slot = slots[0]
    artifacts = {}
    for tag, path in (("reference", args.reference), ("strict", args.strict)):
        entries = torch.load(path, map_location="cpu", weights_only=False)
        matching = [value for value in entries if value["manifest_index"] == 83]
        if len(matching) != 1:
            raise ValueError("Artifact row differs")
        entry = matching[0]
        axis = entry["axis"]
        if (entry["artifact_contract"] != "m95_manifest_native_query_artifact_v1"
                or axis["native_input_sha256"] != expected
                or axis["checkpoint_sha256"] != CHECKPOINT_SHA256
                or axis["scene"] != row["scene_id"]
                or axis["ann_id"] != row["ann_id"]):
            raise ValueError("Artifact identity differs")
        artifacts[tag] = entry
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    gorilla.set_random_seed(1999)
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
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
        raise ValueError("Native feature reduction binding differs")
    held = {}
    hooks = [
        model.output_layer.register_forward_hook(
            lambda module, inputs, result:
            held.update(backbone=result.features.detach().clone())),
        model.dec.input_proj.register_forward_pre_hook(
            lambda module, inputs: held.update(raw_3d=inputs[0].detach().clone())),
        model.criterion.register_forward_pre_hook(
            lambda module, inputs: held.update(pred=inputs[0], offsets=inputs[9],
                                                gt=inputs[1])),
    ]
    records = []
    try:
        with torch.no_grad():
            for arm in ("native", "cpu_reduction"):
                for repeat in range(args.repeats):
                    held.clear()
                    gorilla.set_random_seed(1999)

                    def traced_scatter(source, index, *pos, **kwargs):
                        call = {"source_sha256": digest(source),
                                "index_sha256": digest(index),
                                "source_shape": list(source.shape),
                                "index_shape": list(index.shape)}
                        if arm == "cpu_reduction":
                            reduced = scatter_mean(source.cpu(), index.cpu(),
                                                   *pos, **kwargs).to(source.device)
                        else:
                            reduced = scatter_mean(source, index, *pos, **kwargs)
                        call["output_sha256"] = digest(reduced)
                        call["output_shape"] = list(reduced.shape)
                        held.setdefault("scatter_calls", []).append(call)
                        return reduced

                    network.scatter_mean = traced_scatter
                    loss, _ = model(batch, mode="loss")
                    if not bool(torch.isfinite(loss)):
                        raise ValueError("Nonfinite loss")
                    if len(held["scatter_calls"]) < 2:
                        raise ValueError("Missing feature/coordinate scatter")
                    offsets = held["offsets"]
                    n = int(offsets[slot + 1] - offsets[slot])
                    feature = model.dec.get_batches(held["raw_3d"], offsets)[0][slot, :n].cpu()
                    pred = held["pred"]
                    logits = pred["masks"][slot, query, :n].detach().cpu()
                    scores = pred["indis"][slot].softmax(-1)[:, 1]
                    selected = int(scores.argmax())
                    target = held["gt"][slot].reshape(-1).bool().cpu()
                    selected_mask = pred["masks"][slot, selected, :n].detach().cpu() > 0
                    selected_iou = float(
                        (selected_mask & target).sum().float()
                        / (selected_mask | target).sum().clamp_min(1))
                    comparisons = {}
                    for tag, artifact in artifacts.items():
                        frozen = artifact["features"]["raw_3d"]
                        if feature.shape != frozen.shape or len(artifact["target_union"]) != n:
                            raise ValueError("Artifact support differs")
                        if not torch.equal(artifact["target_union"].bool(),
                                           held["gt"][slot].reshape(-1).bool().cpu()):
                            raise ValueError("Artifact target differs")
                        comparisons[tag] = {
                            "raw_3d_max_abs": float((feature - frozen).abs().max()),
                            "point169_logit": float(artifact["query_mask_logits"][query, 169]),
                            "probe_changed_points": int(((logits > 0) !=
                                (artifact["query_mask_logits"][query] > 0)).sum()),
                        }
                    records.append({
                        "arm": arm, "repeat": repeat, "loss": float(loss),
                        "backbone_sha256": digest(held["backbone"]),
                        "p2v_map_sha256": digest(batch["p2v_map"]),
                        "superpoints_sha256": digest(batch["superpoints"]),
                        "scatter_calls": held["scatter_calls"],
                        "raw_3d_sha256": digest(feature),
                        "point169_logit": float(logits[169]),
                        "selected_query": selected,
                        "selected_iou": selected_iou,
                        "comparisons": comparisons,
                    })
    finally:
        network.scatter_mean = scatter_mean
        for hook in hooks:
            hook.remove()
    output.write_text(json.dumps({
        "contract": "m95_superpoint_reduction_trace_v1",
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "config_sha256": CONFIG_SHA256,
        "model_source_sha256": MODEL_SHA256,
        "batch_sha256": sha256(args.batch),
        "native_item_sha256": expected,
        "artifact_sha256": {tag: sha256(path) for tag, path in
                            (("reference", args.reference), ("strict", args.strict))},
        "manifest_index": 83, "expression_slot": slot,
        "records": records,
        "reference_upstream_hash_available": False,
        "strict_comparator": "unchanged_fail_26_of_65",
        "admission": False,
    }, indent=2, allow_nan=False) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
