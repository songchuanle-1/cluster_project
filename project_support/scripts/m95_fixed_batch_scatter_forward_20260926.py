"""Diagnostic-only fixed-item M95 forward with coordinate scatter control."""
import argparse
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys


CHECKPOINT_SHA256 = "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
MANIFEST_SHA256 = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
CONFIG_SHA256 = "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
MODEL_SHA256 = "cf4ce01548cecf186ba4677f5c13977f9fa527b2e33af6c82f564a7150a4c1d0"
MODEL_NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
QUERIES = {83: 103, 174: 87}


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
    for name in ("root", "bundle", "manifest", "checkpoint", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--row", type=int, choices=tuple(QUERIES), required=True)
    parser.add_argument("--repeats", type=int, default=4)
    parser.add_argument("--trace-ila", action="store_true")
    args = parser.parse_args()
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "7":
        raise ValueError("Authorized physical GPU7 required")
    if not 2 <= args.repeats <= 8:
        raise ValueError("Bounded repeat count required")
    root, bundle = Path(args.root).resolve(), Path(args.bundle).resolve()
    output = Path(args.output)
    if output.exists():
        raise ValueError("Output already exists")
    sys.path[:0] = [str(bundle), str(root), str(root / "framework/lib")]
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")

    import gorilla
    import torch
    from torch_scatter import scatter_mean as native_scatter_mean
    from framework.dataset import build_dataset
    from frozen_capture_contract_20260916 import fingerprint, model_package_sha256
    from native_manifest_capture_20260922 import load_manifest, manifest_dataset_indices

    config = root / "configs/Quard/ctf_hcg_csort" / (MODEL_NAME + ".yaml")
    if sha256(config) != CONFIG_SHA256 or sha256(args.checkpoint) != CHECKPOINT_SHA256:
        raise ValueError("Config or checkpoint identity differs")
    if model_package_sha256(root, MODEL_NAME) != MODEL_SHA256:
        raise ValueError("Model package identity differs")
    manifest = load_manifest(args.manifest, MANIFEST_SHA256)
    target = next(value for value in manifest.rows.values()
                  if value["manifest_index"] == args.row)
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("fixed_batch"))
    indices = manifest_dataset_indices(dataset, manifest)
    dataset_index = next(
        i for i in indices
        if any(str(ann["scene_id"]) == target["scene_id"]
               and int(ann["ann_id"]) == int(target["ann_id"])
               for ann in dataset.scene_inputs[i])
    )
    item = dataset[dataset_index]
    item_sha = fingerprint(item)
    batch = dataset.collate_fn([item])
    if len(batch["scan_ids"]) != 1 or str(batch["scan_ids"][0]) != target["scene_id"]:
        raise ValueError("Target scene binding differs")
    expression_indices = [
        i for i, ann in enumerate(batch["ann_ids"])
        if int(ann) == int(target["ann_id"])
    ]
    if len(expression_indices) != 1:
        raise ValueError("Target expression binding differs")
    expression_index = expression_indices[0]
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
    network_module = importlib.import_module(
        "framework.model.Quard_model." + MODEL_NAME + ".network"
    )
    hierarchy_module = importlib.import_module(
        "framework.model.Quard_model." + MODEL_NAME + ".hier_postprocess"
    )
    if network_module.scatter_mean is not native_scatter_mean:
        raise ValueError("Unexpected scatter_mean binding")
    if hierarchy_module.scatter_mean is not native_scatter_mean:
        raise ValueError("Unexpected hierarchy scatter_mean binding")
    held = {}
    hook = model.criterion.register_forward_pre_hook(
        lambda module, inputs: held.update(pred=inputs[0], offsets=inputs[9])
    )
    raw_hook = model.dec.input_proj.register_forward_hook(
        lambda module, inputs, result: held.update(raw_3d=inputs[0].detach())
    )
    projected_hook = model.dec.input_proj.register_forward_hook(
        lambda module, inputs, result: held.update(projected_3d=result.detach())
    )
    fused_hook = model.dec.sum_norm.register_forward_hook(
        lambda module, inputs, result: held.update(fused=result.detach())
    )
    final_hook = model.dec.encoder_layers[-1].register_forward_hook(
        lambda module, inputs, result: held.update(final_3d=result[1].detach())
    )
    encoder_hooks = []
    for layer_index, layer in enumerate(model.dec.encoder_layers):
        def capture_input(module, inputs, index=layer_index):
            held.setdefault("encoder_inputs", {})[index] = digest(inputs[2])

        def capture_output(module, inputs, result, index=layer_index):
            held.setdefault("encoder_outputs", {})[index] = digest(result[1])

        encoder_hooks.append(layer.register_forward_pre_hook(capture_input))
        encoder_hooks.append(layer.register_forward_hook(capture_output))
    final_layer = model.dec.encoder_layers[-1]
    stage_hooks = []
    reference_message = {}
    reference_cluster_feats = {}
    if args.trace_ila:
        def capture_cluster_inputs(module, inputs):
            feats = inputs[3]
            held["cluster_input_sha256"] = {
                "point": digest(inputs[0]),
                "query": digest(inputs[1]),
                "feats": [digest(value) for value in feats],
            }
            if held.get("replay_feats"):
                if len(feats) != len(reference_cluster_feats["feats"]):
                    raise ValueError("Cluster feature replay scale count differs")
                if any(a.shape != b.shape for a, b in
                       zip(feats, reference_cluster_feats["feats"])):
                    raise ValueError("Cluster feature replay shape differs")
                return (*inputs[:3], reference_cluster_feats["feats"], *inputs[4:])
            if held.get("save_feats"):
                reference_cluster_feats["feats"] = [value.detach().clone() for value in feats]

        def capture_cluster(module, inputs, result):
            message = result["point"]
            held["cluster_message"] = digest(message)
            if held.get("replay_message"):
                if message.shape != reference_message["point"].shape:
                    raise ValueError("Cluster message replay shape differs")
                result = dict(result)
                result["point"] = reference_message["point"]
            elif held.get("save_message"):
                reference_message["point"] = message.detach().clone()
            return result

        def capture_ila_inputs(module, inputs):
            held["ila_input_sha256"] = [digest(inputs[0]), digest(inputs[1])]

        stage_hooks.append(final_layer.cluster_att.register_forward_pre_hook(capture_cluster_inputs))
        stage_hooks.append(final_layer.cluster_att.register_forward_hook(capture_cluster))
        stage_hooks.append(final_layer.ila.register_forward_pre_hook(capture_ila_inputs))
    for name in ("lla", "lia", "cluster_bank", "cluster_att", "ila", "lia_ffn"):
        module = getattr(final_layer, name, None)
        if module is None:
            continue

        def capture_stage(module, inputs, result, stage=name):
            tensors = result if isinstance(result, (tuple, list)) else (result,)
            held.setdefault("stage_outputs", {})[stage] = [
                digest(value) for value in tensors if torch.is_tensor(value)
            ]

        stage_hooks.append(module.register_forward_hook(capture_stage))
    rows = []
    try:
        with torch.no_grad():
            arms = ("gpu_native", "cpu_coords", "cpu_all_scatter")
            if args.trace_ila:
                arms += ("cpu_all_scatter_cluster_cpu",
                         "cpu_all_scatter_replay_feats",
                         "cpu_all_scatter_replay_message")
            for arm in arms:
                for repeat in range(args.repeats):
                    gorilla.set_random_seed(1999)
                    calls = []

                    def scatter(source, index, *pos, **kw):
                        if source.ndim == 2 and source.shape[1] == 3:
                            if arm in ("cpu_coords", "cpu_all_scatter",
                                       "cpu_all_scatter_cluster_cpu",
                                       "cpu_all_scatter_replay_feats",
                                       "cpu_all_scatter_replay_message"):
                                value = native_scatter_mean(
                                    source.cpu(), index.cpu(), *pos, **kw
                                ).to(source.device)
                            else:
                                value = native_scatter_mean(source, index, *pos, **kw)
                            calls.append(digest(value))
                            return value
                        if arm in ("cpu_all_scatter", "cpu_all_scatter_cluster_cpu",
                                   "cpu_all_scatter_replay_feats",
                                   "cpu_all_scatter_replay_message"):
                            return native_scatter_mean(
                                source.cpu(), index.cpu(), *pos, **kw
                            ).to(source.device)
                        return native_scatter_mean(source, index, *pos, **kw)

                    network_module.scatter_mean = scatter
                    if arm == "cpu_all_scatter_cluster_cpu":
                        def hierarchy_scatter(source, index, *pos, **kw):
                            return native_scatter_mean(
                                source.cpu(), index.cpu(), *pos, **kw
                            ).to(source.device)
                        hierarchy_module.scatter_mean = hierarchy_scatter
                    else:
                        hierarchy_module.scatter_mean = native_scatter_mean
                    held.clear()
                    if args.trace_ila:
                        held["save_message"] = arm == "cpu_all_scatter" and repeat == 0
                        held["replay_message"] = arm == "cpu_all_scatter_replay_message"
                        held["save_feats"] = arm == "cpu_all_scatter" and repeat == 0
                        held["replay_feats"] = arm == "cpu_all_scatter_replay_feats"
                        if held["replay_message"] and "point" not in reference_message:
                            raise ValueError("Missing reference cluster message")
                        if held["replay_feats"] and "feats" not in reference_cluster_feats:
                            raise ValueError("Missing reference cluster features")
                    loss, _ = model(batch, mode="loss")
                    if len(calls) != 1 or not bool(torch.isfinite(loss)):
                        raise ValueError("Coordinate scatter call or native loss differs")
                    pred = held["pred"]
                    if len(pred["masks"]) <= expression_index or len(pred["masks"][expression_index]) <= QUERIES[args.row]:
                        raise ValueError("Query axis differs")
                    n = int(held["offsets"][expression_index + 1] - held["offsets"][expression_index])
                    logits = pred["masks"][expression_index, QUERIES[args.row], :n].detach()
                    scores = pred["indis"][expression_index].softmax(-1)[:, 1].detach()
                    if not torch.isfinite(logits).all() or not torch.isfinite(scores).all():
                        raise ValueError("Nonfinite native outputs")
                    rows.append({
                        "arm": arm,
                        "repeat": repeat,
                        "coordinate_sha256": calls[0],
                        "raw_3d_sha256": digest(held["raw_3d"]),
                        "projected_3d_sha256": digest(held["projected_3d"]),
                        "fused_sha256": digest(held["fused"]),
                        "final_3d_sha256": digest(held["final_3d"]),
                        "encoder_input_sha256": [
                            held["encoder_inputs"][i] for i in range(len(model.dec.encoder_layers))
                        ],
                        "encoder_output_sha256": [
                            held["encoder_outputs"][i] for i in range(len(model.dec.encoder_layers))
                        ],
                        "final_layer_stages": dict(held.get("stage_outputs", {})),
                        **({"cluster_input_sha256": held["cluster_input_sha256"],
                            "cluster_message_sha256": held["cluster_message"],
                            "ila_input_sha256": held["ila_input_sha256"]}
                           if args.trace_ila else {}),
                        "fps_sha256": digest(pred["sample_inds"][expression_index]),
                        "query_logit_sha256": digest(logits),
                        "query_mask_sha256": digest(logits > 0),
                        "selected_query": int(scores.argmax()),
                        "query_logit_min_abs": float(logits.abs().min()),
                        "query_mask_points": int((logits > 0).sum()),
                        "loss": float(loss),
                    })
    finally:
        network_module.scatter_mean = native_scatter_mean
        hierarchy_module.scatter_mean = native_scatter_mean
        hook.remove()
        raw_hook.remove()
        projected_hook.remove()
        fused_hook.remove()
        final_hook.remove()
        for encoder_hook in encoder_hooks:
            encoder_hook.remove()
        for stage_hook in stage_hooks:
            stage_hook.remove()
    result = {
        "contract": "m95_fixed_batch_ila_trace_v1" if args.trace_ila else "m95_fixed_batch_scatter_forward_v1",
        "scope": "One transformed TRAIN item, repeated native M95 loss forward; CPU coordinate reduction is an opt-in diagnostic intervention",
        "manifest_index": args.row,
        "dataset_index": dataset_index,
        "expression_index": expression_index,
        "native_item_sha256": item_sha,
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "manifest_sha256": MANIFEST_SHA256,
        "config_sha256": CONFIG_SHA256,
        "model_source_sha256": MODEL_SHA256,
        "rows": rows,
        "strict_reproducibility_status": "fail",
        "admission": False,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
