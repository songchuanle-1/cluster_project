"""Native loss-component Jacobians; never performs an optimizer step."""
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


def similarity(torch, left, right):
    a, b = left.double().flatten(), right.double().flatten()
    dot = float(a.dot(b))
    norms = [float(a.norm()), float(b.norm())]
    return {"dot": dot, "norms": norms,
            "cosine": dot / (norms[0] * norms[1]) if min(norms) > 0 else None}


def components(torch, loss_dict, weights):
    return {
        "mask": weights[0] * loss_dict["mask_bce_loss"]
        + weights[1] * loss_dict["mask_dice_loss"],
        "referent": weights[4] * loss_dict["indi_loss"],
        "semantic": weights[6] * loss_dict["sem_loss"],
        "quality": weights[2] * loss_dict["score_loss"],
    }


def flat_parameter_grad(torch, loss, parameters):
    grads = (torch.autograd.grad(loss, parameters, retain_graph=True,
                                allow_unused=True) if loss.requires_grad
             else (None,) * len(parameters))
    return torch.cat([(torch.zeros_like(p) if g is None else g).flatten()
                      for p, g in zip(parameters, grads)]), {
        "total_tensors": len(parameters),
        "connected_tensors": sum(g is not None for g in grads),
        "nonzero_tensors": sum(g is not None and bool(g.count_nonzero()) for g in grads),
        "finite_tensors": sum(g is not None and bool(torch.isfinite(g).all()) for g in grads),
    }


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
        raise ValueError("Native source hashes differ")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import torch
    import gorilla
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader
    from m95_final_seed_target_probe_20260927 import batch_fingerprint

    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.30)
    cfg = gorilla.Config.fromfile(str(
        root / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")))
    cfg.model.data_root = cfg.data.train.data_root = str(data_root) + "/"
    gorilla.set_random_seed(1999)
    source = build_dataset(cfg.data.train, logging.getLogger("native_task_jacobian"))
    indices = select_native_indices(source, frozen)
    model = importlib.import_module("framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    held = {}
    handles = [
        model.dec.decoder_layers[-1].out_norm.register_forward_pre_hook(
            lambda module, values: held.update(query=values[0])),
        model.criterion.register_forward_pre_hook(
            lambda module, values: held.update(pred=values[0])),
    ]
    params = list(model.dec.decoder_layers[-1].qqa_ffn.parameters())
    rows, parameter_rows = [], []
    started = time.time()
    try:
        for repeat in range(2):
            gorilla.set_random_seed(1999)
            loader = selected_loader(source, indices, DataLoader)
            for batch_index, batch in enumerate(loader):
                fingerprint = batch_fingerprint(torch, batch)
                held.clear()
                gorilla.set_random_seed(1999)
                loss, loss_dict = model(batch, mode="loss")
                if not bool(torch.isfinite(loss).all()):
                    raise ValueError("Nonfinite native loss")
                query, pred = held["query"], held["pred"]
                parts = components(torch, loss_dict, model.criterion.loss_weight)
                query_grads, parameter_grads, param_checks = {}, {}, {}
                for key, part in parts.items():
                    grad = (torch.autograd.grad(part, query, retain_graph=True,
                                                allow_unused=True)[0]
                            if part.requires_grad else None)
                    query_grads[key] = torch.zeros_like(query) if grad is None else grad
                    parameter_grads[key], param_checks[key] = flat_parameter_grad(torch, part, params)
                total = torch.autograd.grad(loss, query, retain_graph=True)[0]
                recon = sum(query_grads.values())
                error = float((total - recon).abs().max())
                if error > 2e-5 or not bool(torch.isfinite(total).all()):
                    raise ValueError("Actual query gradient reconstruction failed: %g" % error)
                pairs = (("mask", "referent"), ("mask", "semantic"), ("referent", "semantic"))
                parameter_rows.append({
                    "repeat": repeat, "batch": batch_index,
                    "components": param_checks,
                    "pairs": {a + "/" + b: similarity(torch, parameter_grads[a], parameter_grads[b])
                              for a, b in pairs},
                })
                scenes = [scene for scene, count in zip(batch["scan_ids"], batch["scenes_len"])
                          for _ in range(int(count))]
                for b, (scene, aid) in enumerate(zip(scenes, batch["ann_ids"])):
                    key = scene, int(aid)
                    target = batch["gt_spmasks"][b].to(query.device).flatten().bool()
                    selected = int(pred["indis"][b].softmax(-1)[:, 1].argmax())
                    mask = pred["masks"][b, selected, :len(target)] > 0
                    row = {
                        "repeat": repeat, "batch": batch_index, "scene": scene,
                        "ann_id": int(aid), "frozen": key in frozen,
                        "batch_input_sha256": fingerprint, "native_loss": float(loss.detach()),
                        "query_gradient_sum_error": error,
                        "selected_mask_iou": float((mask & target).sum() / (mask | target).sum().clamp_min(1)),
                        "pairs": {}, "descent": {},
                    }
                    for a, other in pairs:
                        row["pairs"][a + "/" + other] = {
                            "native": similarity(torch, query_grads[a][b], query_grads[other][b]),
                            "rotated": similarity(torch, query_grads[a][b], query_grads[other][b].roll(1, 0)),
                        }
                    for name, grad in query_grads.items():
                        row["descent"][name] = similarity(torch, grad[b], total[b])
                    rows.append(row)
                print(json.dumps({"repeat": repeat, "batch": batch_index,
                                  "loss": float(loss.detach()), "sum_error": error}), flush=True)
                del loss, loss_dict, query_grads, parameter_grads, total, recon, query, pred
                held.clear()
    finally:
        for handle in handles:
            handle.remove()
    for repeat in range(2):
        selected = [row for row in rows if row["repeat"] == repeat and row["frozen"]]
        if len(selected) != 31 or len({(r["scene"], r["ann_id"]) for r in selected}) != 31:
            raise ValueError("Frozen expression coverage differs")
    payload = {
        "contract": "m95_native_task_jacobian_v1", "admission": False,
        "checkpoint_sha256": sha(args.checkpoint), "manifest_sha256": sha(args.manifest),
        "script_sha256": sha(Path(__file__)), "native_sources": expected,
        "loader_batches": len(indices), "rows": rows, "parameter_rows": parameter_rows,
        "elapsed_seconds": time.time() - started,
        "peak_allocated_mib": torch.cuda.max_memory_allocated() / (1024 ** 2),
        "training_started": False,
    }
    with output.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(output), "sha256": sha(output), "rows": len(rows)}))


if __name__ == "__main__":
    main()
