"""Matched frozen M95 batch control for cluster-bank scatter repeatability."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys


CHECKPOINT_SHA256 = "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
CONFIG_SHA256 = "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
MODEL_SHA256 = "cf4ce01548cecf186ba4677f5c13977f9fa527b2e33af6c82f564a7150a4c1d0"
MODEL_NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
EXPECTED = {
    83: ("a39cfebecda7333f23c3abcf9bdd0029bee13be070305a604d195397fdbc068c", 103),
    174: ("a7bbf63a74172c28bfc0cb1076377cd66d0df9380516a2ebb4d1bbc4cc5449b7", 87),
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def digest(tensor):
    return hashlib.sha256(tensor.detach().cpu().contiguous().numpy().tobytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ("root", "bundle", "checkpoint", "batch", "manifest", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--row", type=int, choices=tuple(EXPECTED), required=True)
    parser.add_argument("--repeats", type=int, default=4)
    parser.add_argument("--artifact")
    args = parser.parse_args()
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "7" or not 2 <= args.repeats <= 8:
        raise ValueError("Authorized GPU7 and bounded repeats required")
    output = Path(args.output)
    if output.exists():
        raise ValueError("Output already exists")
    root = Path(args.root).resolve()
    sys.path[:0] = [str(Path(args.bundle).resolve()),
                    str(Path(__file__).resolve().parent), str(root),
                    str(root / "framework/lib")]
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    import gorilla
    import torch
    from torch_scatter import scatter_mean as native_scatter_mean
    from frozen_capture_contract_20260916 import model_package_sha256
    from native_manifest_capture_20260922 import load_manifest

    config = root / "configs/Quard/ctf_hcg_csort" / (MODEL_NAME + ".yaml")
    if (sha256(config) != CONFIG_SHA256 or sha256(args.checkpoint) != CHECKPOINT_SHA256
            or model_package_sha256(root, MODEL_NAME) != MODEL_SHA256):
        raise ValueError("Frozen model identity differs")
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

    saved = torch.load(args.batch, map_location="cpu", weights_only=False)
    expected_hash, query = EXPECTED[args.row]
    if (saved["contract"] != "m95_frozen_target_batch_v1"
            or saved["manifest_index"] != args.row
            or saved["native_item_sha256"] != expected_hash
            or saved["frozen_native_input_sha256"] != expected_hash):
        raise ValueError("Frozen batch binding differs")
    batch = saved["batch"]
    manifest = load_manifest(args.manifest,
                             "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023")
    target_row = next(row for row in manifest.rows.values()
                      if row["manifest_index"] == args.row)
    target_scene = target_row["scene_id"]
    target_ann = target_row["ann_id"]
    scene_slots = [str(x) for x in batch["scan_ids"]]
    scene_lengths = [int(x) for x in batch["scenes_len"]]
    if len(scene_slots) != 2 or len(scene_lengths) != 2:
        raise ValueError("Expected original two-scene batch")
    if target_scene not in scene_slots:
        raise ValueError("Target scene absent from frozen batch")
    scene_index = scene_slots.index(target_scene)
    slots = [slot for slot in range(sum(scene_lengths[:scene_index]),
                                   sum(scene_lengths[:scene_index + 1]))
             if int(batch["ann_ids"][slot]) == target_ann]
    if len(slots) != 1:
        raise ValueError("Frozen target expression not uniquely bound")
    artifact = None
    if args.artifact:
        payload = torch.load(args.artifact, map_location="cpu", weights_only=False)
        matching = [row for row in payload if row["manifest_index"] == args.row]
        if len(matching) != 1:
            raise ValueError("Full-scan artifact row not unique")
        artifact = matching[0]
        axis = artifact["axis"]
        if (artifact["artifact_contract"] != "m95_manifest_native_query_artifact_v1"
                or axis["scene"] != target_scene or axis["ann_id"] != target_ann
                or axis["native_input_sha256"] != expected_hash
                or axis["checkpoint_sha256"] != CHECKPOINT_SHA256):
            raise ValueError("Full-scan artifact identity differs")
    held = {}
    hook = model.criterion.register_forward_pre_hook(
        lambda module, inputs: held.update(pred=inputs[0], gt=inputs[1],
                                            offsets=inputs[9])
    )
    def sparse_digest(value):
        if isinstance(value, (tuple, list)):
            value = value[0]
        return digest(value.features if hasattr(value, "features") else value)

    backbone_hooks = []
    for name in ("input_conv", "unet", "output_layer"):
        module = getattr(model, name)
        backbone_hooks.append(module.register_forward_pre_hook(
            lambda module, inputs, stage=name:
            held.setdefault("backbone_inputs", {}).update(
                {stage: sparse_digest(inputs[0])})))
        backbone_hooks.append(module.register_forward_hook(
            lambda module, inputs, result, stage=name:
            held.setdefault("backbone_outputs", {}).update(
                {stage: sparse_digest(result)})))
    feature_hooks = [
        model.dec.input_proj.register_forward_hook(
            lambda module, inputs, result: held.update(raw_3d=inputs[0].detach())),
        model.dec.sum_norm.register_forward_hook(
            lambda module, inputs, result: held.update(fused=result.detach())),
        model.dec.encoder_layers[-1].register_forward_hook(
            lambda module, inputs, result: held.update(final=result[1].detach())),
    ]
    network_module = importlib.import_module(
        "framework.model.Quard_model." + MODEL_NAME + ".network"
    )
    hierarchy_module = importlib.import_module(
        "framework.model.Quard_model." + MODEL_NAME + ".hier_postprocess"
    )
    if (network_module.scatter_mean is not native_scatter_mean
            or hierarchy_module.scatter_mean is not native_scatter_mean):
        raise ValueError("Unexpected scatter binding")
    rows = []
    try:
        with torch.no_grad():
            for arm in ("native", "native_cluster_cpu", "cpu_all_scatter",
                        "cpu_all_scatter_cluster_cpu"):
                for repeat in range(args.repeats):
                    gorilla.set_random_seed(1999)
                    held.clear()
                    if arm.startswith("cpu_all_scatter"):
                        def network_scatter(source, index, *pos, **kw):
                            return native_scatter_mean(
                                source.cpu(), index.cpu(), *pos, **kw
                            ).to(source.device)
                        network_module.scatter_mean = network_scatter
                    else:
                        network_module.scatter_mean = native_scatter_mean
                    if arm in ("native_cluster_cpu", "cpu_all_scatter_cluster_cpu"):
                        def cluster_scatter(source, index, *pos, **kw):
                            return native_scatter_mean(
                                source.cpu(), index.cpu(), *pos, **kw
                            ).to(source.device)
                        hierarchy_module.scatter_mean = cluster_scatter
                    else:
                        hierarchy_module.scatter_mean = native_scatter_mean
                    loss, _ = model(batch, mode="loss")
                    if not bool(torch.isfinite(loss)):
                        raise ValueError("Nonfinite native loss")
                    pred = held["pred"]
                    for slot in slots:
                        n = int(held["offsets"][slot + 1] - held["offsets"][slot])
                        masks = pred["masks"][slot, :, :n] > 0
                        gt = held["gt"][slot].reshape(-1).bool()
                        if len(gt) != n:
                            raise ValueError("Target support differs")
                        scores = pred["indis"][slot].softmax(-1)[:, 1]
                        selected = int(scores.argmax())
                        comparison = {}
                        if artifact is not None:
                            frozen_logits = artifact["query_mask_logits"]
                            if (tuple(frozen_logits.shape) != tuple(pred["masks"][slot, :, :n].shape)
                                    or len(artifact["target_union"]) != n
                                    or not torch.equal(artifact["target_union"].bool(),
                                                       gt.cpu())):
                                raise ValueError("Frozen artifact support differs")
                            replay_logits = pred["masks"][slot, :, :n].detach().cpu()
                            comparison = {
                                "artifact_query_logit_max_abs": float(
                                    (replay_logits[query] - frozen_logits[query]).abs().max()),
                                "artifact_score_max_abs": float(
                                    (scores.detach().cpu() - artifact["query_scores"]).abs().max()),
                                "artifact_query_mask_changed_points": int(
                                    ((replay_logits[query] > 0)
                                     != (frozen_logits[query] > 0)).sum()),
                                "artifact_selected_query": int(
                                    artifact["query_scores"].argmax()),
                                "artifact_point169_logit": (
                                    float(frozen_logits[query, 169])
                                    if args.row == 83 and n > 169 else None),
                            }
                            for name in ("raw_3d", "fused", "final"):
                                observed = held[name]
                                if observed.ndim == 3:
                                    feature = observed[slot, :n].detach().cpu()
                                else:
                                    feature = model.dec.get_batches(
                                        observed, held["offsets"])[0][slot, :n].detach().cpu()
                                frozen = artifact["features"][name]
                                if feature.shape != frozen.shape:
                                    raise ValueError("Full-scan feature shape differs: " + name)
                                comparison["artifact_" + name + "_max_abs"] = float(
                                    (feature - frozen).abs().max())
                        def iou(mask):
                            return float(((mask & gt).sum().float()
                                          / (mask | gt).sum().clamp_min(1)))
                        rows.append({
                            "arm": arm, "repeat": repeat, "expression_slot": slot,
                            "ann_id": int(batch["ann_ids"][slot]),
                            "selected_query": selected,
                            "selected_iou": iou(masks[selected]),
                            "selected_mask_sha256": digest(masks[selected]),
                            "probe_query": query,
                            "probe_iou": iou(masks[query]),
                            "probe_mask_sha256": digest(masks[query]),
                            "probe_mask_points": int(masks[query].sum()),
                            "probe_min_abs_logit": float(
                                pred["masks"][slot, query, :n].abs().min()),
                            "probe_point169_logit": (
                                float(pred["masks"][slot, query, 169])
                                if args.row == 83 and n > 169 else None),
                            "probe_point169_target": (
                                bool(gt[169])
                                if args.row == 83 and n > 169 else None),
                            "score_sha256": digest(scores),
                            "backbone_inputs": dict(held["backbone_inputs"]),
                            "backbone_outputs": dict(held["backbone_outputs"]),
                            "loss": float(loss),
                            **comparison,
                        })
    finally:
        network_module.scatter_mean = native_scatter_mean
        hierarchy_module.scatter_mean = native_scatter_mean
        hook.remove()
        for backbone_hook in backbone_hooks:
            backbone_hook.remove()
        for feature_hook in feature_hooks:
            feature_hook.remove()
    result = {
        "contract": "m95_frozen_batch_cluster_control_v1",
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "config_sha256": CONFIG_SHA256,
        "model_source_sha256": MODEL_SHA256,
        "saved_batch_sha256": sha256(args.batch),
        "native_item_sha256": expected_hash,
        "manifest_index": args.row,
        "target_scene": target_scene,
        "target_ann_id": target_ann,
        "artifact_sha256": sha256(args.artifact) if artifact is not None else None,
        "rows": rows,
        "strict_fullscan_comparator": "unchanged_fail_26_of_65",
        "admission": False,
    }
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                      encoding="ascii")


if __name__ == "__main__":
    main()
