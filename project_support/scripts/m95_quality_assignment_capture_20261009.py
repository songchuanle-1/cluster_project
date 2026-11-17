"""Frozen native quality-coverage and depth-assignment diagnostic, no optimizer."""
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


def index_hash(indices):
    encoded = [(q.detach().cpu().tolist(), t.detach().cpu().tolist())
               for q, t in indices]
    return hashlib.sha256(json.dumps(encoded, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ("root", "checkpoint", "manifest", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    if (os.environ.get("CUDA_VISIBLE_DEVICES") != "7" or output.exists()
            or not output.is_relative_to(root.parent / "pipeline")
            or sha(args.checkpoint) != CHECKPOINT_SHA):
        raise ValueError("GPU7, frozen checkpoint and fresh project output required")
    frozen = frozen_rows(args.manifest)
    data_root = Path("/data3/songcl/data/data_cluster")
    expected = {
        "dataset": DATASET_SHA, "annotations": ANNOTATION_SHA, "graphs": GRAPH_SHA,
        "loss": "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5",
        "decoder": "6f7566bd02121fd218fd1360be7c7b1905c267de8a03f36473779ab4d66b9d3a",
        "network": "5a77eb852b3c6e5de2804d80a2c7a16504f1fd8a57aa94dc6045d9f35587625d",
    }
    package = root / "framework/model/Quard_model" / NAME
    paths = {
        "dataset": root / "framework/dataset/scannetv2.py",
        "annotations": data_root / "scanrefer/ScanRefer_train_new.json",
        "graphs": data_root / "scanrefer/scene_graphs_new_train.json",
        "loss": package / "loss.py", "decoder": package / "dec.py",
        "network": package / "network.py",
    }
    if {key: sha(path) for key, path in paths.items()} != expected:
        raise ValueError("Frozen native source hashes differ")
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
    config_path = root / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")
    cfg = gorilla.Config.fromfile(str(config_path))
    cfg.model.data_root = cfg.data.train.data_root = str(data_root) + "/"
    gorilla.set_random_seed(1999)
    source = build_dataset(cfg.data.train, logging.getLogger("quality_assignment"))
    indices = select_native_indices(source, frozen)
    model = importlib.import_module("framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    loss_module = importlib.import_module("framework.model.Quard_model." + NAME + ".loss")
    original = model.criterion.loss_masks
    held = {}
    hook = model.criterion.register_forward_pre_hook(
        lambda module, inputs: held.update(pred=inputs[0]))
    batch_layers = []

    def capture(masks, scores, targets, matched, normalizer):
        rows = []
        for b, (mask, score, target, (qids, tids)) in enumerate(
                zip(masks, scores, targets, matched)):
            if target["masks"] is None:
                rows.append({"batch_row": b, "missing_target": True})
                continue
            quality = loss_module.get_iou(mask[qids], target["masks"][tids])
            eligible = quality > 0.5
            rows.append({
                "batch_row": b, "missing_target": False,
                "queries": len(score), "matched": len(qids),
                "supervised": int(eligible.sum()),
                "censored": int((~eligible).sum()),
                "qids": qids.detach().cpu().tolist(),
                "quality": quality.detach().cpu().tolist(),
                "scores": score[qids].detach().flatten().cpu().tolist(),
            })
        batch_layers.append({"assignment_sha256": index_hash(matched), "rows": rows})
        return original(masks, scores, targets, matched, normalizer)

    model.criterion.loss_masks = capture
    records, batches = [], []
    started = time.time()
    try:
        for repeat in range(2):
            gorilla.set_random_seed(1999)
            loader = selected_loader(source, indices, DataLoader)
            for batch_index, batch in enumerate(loader):
                batch_layers.clear()
                held.clear()
                fingerprint = batch_fingerprint(torch, batch)
                gorilla.set_random_seed(1999)
                loss, losses = model(batch, mode="loss")
                pred = held["pred"]
                if not bool(torch.isfinite(loss).all()):
                    raise ValueError("Nonfinite native loss")
                final_scores = pred["scores"]
                quality_loss = model.criterion.loss_weight[2] * losses["score_loss"]
                grad = (torch.autograd.grad(quality_loss, final_scores,
                                           retain_graph=True, allow_unused=True)[0]
                        if quality_loss.requires_grad else None)
                score_grad = torch.zeros_like(final_scores) if grad is None else grad
                scenes = [scene for scene, count in zip(batch["scan_ids"], batch["scenes_len"])
                          for _ in range(int(count))]
                final = batch_layers[0]
                for b, (scene, ann_id) in enumerate(zip(scenes, batch["ann_ids"])):
                    row = final["rows"][b]
                    target = batch["gt_spmasks"][b].to(final_scores.device).flatten().bool()
                    selected = int(pred["indis"][b].softmax(-1)[:, 1].argmax())
                    mask = pred["masks"][b, selected, :len(target)] > 0
                    iou = float((mask & target).sum() / (mask | target).sum().clamp_min(1))
                    row = {
                        **row, "repeat": repeat, "batch": batch_index,
                        "scene": scene, "ann_id": int(ann_id),
                        "frozen": (scene, int(ann_id)) in frozen,
                        "input_sha256": fingerprint, "selected_query": selected,
                        "selected_iou": iou,
                        "score_gradient_nonzero_queries":
                            int(score_grad[b].flatten().ne(0).sum()),
                        "score_gradient_finite": bool(torch.isfinite(score_grad[b]).all()),
                        "selected_is_matched": selected in row.get("qids", []),
                        "all_layer_assignments_identical": all(
                            layer["assignment_sha256"] == final["assignment_sha256"]
                            for layer in batch_layers),
                    }
                    records.append(row)
                batches.append({
                    "repeat": repeat, "batch": batch_index,
                    "input_sha256": fingerprint, "native_loss": float(loss.detach()),
                    "quality_loss": float(quality_loss.detach()),
                    "layer_count": len(batch_layers),
                    "assignments": [item["assignment_sha256"] for item in batch_layers],
                    "rotated_control_differs": any(
                        row.get("qids") and any(q != (q + 1) % row["queries"]
                                               for q in row["qids"])
                        for row in final["rows"]),
                    "layers": [dict(assignment_sha256=item["assignment_sha256"],
                                    matched=sum(r.get("matched", 0) for r in item["rows"]),
                                    censored=sum(r.get("censored", 0) for r in item["rows"]))
                               for item in batch_layers],
                })
                print(json.dumps({"repeat": repeat, "batch": batch_index,
                                  "quality_loss": float(quality_loss.detach())}), flush=True)
                del loss, losses, pred, final_scores, grad, score_grad, quality_loss
                batch_layers.clear()
                held.clear()
    finally:
        hook.remove()
        model.criterion.loss_masks = original
    for repeat in range(2):
        rows = [r for r in records if r["frozen"] and r["repeat"] == repeat]
        if len(rows) != 31 or len({(r["scene"], r["ann_id"]) for r in rows}) != 31:
            raise ValueError("Frozen cohort coverage differs")
    payload = {
        "contract": "m95_quality_assignment_capture_v1", "admission": False,
        "checkpoint_sha256": sha(args.checkpoint),
        "manifest_sha256": sha(args.manifest), "script_sha256": sha(Path(__file__)),
        "native_sources": expected, "config_sha256": sha(config_path),
        "records": records, "batches": batches,
        "elapsed_seconds": time.time() - started,
        "peak_allocated_mib": torch.cuda.max_memory_allocated() / (1024 ** 2),
        "training_started": False,
    }
    with output.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(output), "sha256": sha(output)}))


if __name__ == "__main__":
    main()
