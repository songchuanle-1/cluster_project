"""Read-only capture of final decoder evidence for one frozen checkpoint.

This worker does not modify the model package, training config, queue, or
checkpoint. It replays the frozen diagnostic descriptions and stores the final
candidate masks, the selection head, the discarded quality head, the trained
semantic alignment projections, and the language/visual tensors needed for
offline candidate-evidence tests.
"""
import argparse
import gc
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys
import time

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

MANIFEST_SHA = "84a7d60f85ecd5bec44b77b304140ff00c8c1fa00177dc12ecf7ef5ebfabb468"
BUFFER_KEYS = {
    "text_encoder.embeddings.position_ids",
    "text_encoder.embeddings.token_type_ids",
}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def key(record):
    return record["scene_id"], str(record["object_id"]), str(record["ann_id"])


def rank_of(index, values):
    order = sorted(range(len(values)), key=lambda i: float(values[i]), reverse=True)
    return order.index(index)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-root", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--scene-limit", type=int, default=0)
    args = parser.parse_args()

    root = Path(args.code_root)
    output = Path(args.out)
    assert not output.exists(), "Immutable output directory already exists"
    assert sha(args.manifest) == MANIFEST_SHA
    audit = json.loads(Path(args.audit).read_text(encoding="utf-8"))
    assert sha(audit["checkpoint"]) == audit["checkpoint_sha256"]
    assert sha(audit["config"]) == audit["config_sha256"]
    import subprocess
    assert subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip() == audit["code_head"]

    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import gorilla
    import torch
    from framework.dataset import build_dataset

    torch.set_num_threads(1)
    free, total = torch.cuda.mem_get_info()
    assert free >= 8 * 1024**3, f"Insufficient preflight free memory: {free}"
    torch.cuda.set_per_process_memory_fraction(8 * 1024**3 / total)
    gorilla.set_random_seed(1999)
    cfg = gorilla.Config.fromfile(audit["config"])
    assert cfg.test.seed == 1999
    assert not cfg.data.val.training and cfg.data.val.get("src_sample", -1) == -1

    data_root = Path(cfg.data.val.data_root)
    source = data_root / "scanrefer/ScanRefer_val_new.json"
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    assert sha(source) == manifest["source_sha256"]
    records = json.loads(source.read_text(encoding="utf-8"))
    by_key = {key(record): record for record in records}
    assert len(by_key) == len(records)
    samples = [sample for sample in manifest["samples"] if sample["subset"] == "diagnostic"]
    scenes = sorted({sample["scene_id"] for sample in samples})
    if args.scene_limit:
        scenes = scenes[:args.scene_limit]
    chosen = [sample for sample in samples if sample["scene_id"] in scenes]
    assert len(chosen) == 4 * len(scenes)

    output.mkdir(parents=True)
    logger = logging.getLogger("evidence_capture")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    dataset = build_dataset(cfg.data.val, logger)
    dataset.scene_inputs = [[by_key[key(sample)]] for sample in chosen]

    module = importlib.import_module(audit["explicit_module"])
    package = Path(module.__file__).parent
    assert {path.name: sha(path) for path in sorted(package.glob("*.py"))} == audit["package_sha256"]
    get_iou = importlib.import_module(audit["explicit_module"] + ".loss").get_iou
    model = module.Network(**cfg.model)
    assert model.task_type == "res"
    checkpoint = torch.load(audit["checkpoint"], map_location="cpu", weights_only=False)
    state = checkpoint["model"]
    expected = model.state_dict()
    assert set(state) - set(expected) == BUFFER_KEYS
    assert not set(expected) - set(state)
    for name in BUFFER_KEYS:
        runtime = getattr(model.text_encoder.embeddings, name.rsplit(".", 1)[1])
        assert torch.equal(state[name], runtime)
    model.load_state_dict({name: value for name, value in state.items() if name not in BUFFER_KEYS}, strict=True)
    del state, checkpoint, expected
    gc.collect()
    model.cuda().eval()

    capture = {}

    def pre_hook(module, inputs):
        capture["lang_feats"] = inputs[0].detach()
        capture["lang_masks"] = inputs[1].detach()
        capture["inst_feats"] = inputs[2].detach()
        capture["batch_mask"] = inputs[3].detach()
        capture["query_in"] = inputs[4].detach()

    def post_hook(module, inputs, outputs):
        capture["query"] = outputs[0].detach()
        capture["quality_scores"] = outputs[1].detach()
        capture["mask_logits"] = outputs[2].detach()
        capture["indis_logits"] = outputs[3].detach()
        capture["proj_query"] = outputs[4].detach()
        capture["proj_token"] = outputs[5].detach()

    handle_pre = model.dec.decoder_layers[-1].register_forward_pre_hook(pre_hook)
    handle_post = model.dec.decoder_layers[-1].register_forward_hook(post_hook)
    original_predict = model.predict_by_feat
    rows = []

    def capture_predict(scan_ids, object_idss, ann_ids, out, superpoints,
                        gt_pmasks, gt_spmasks, fps_seed_sp):
        result = original_predict(
            scan_ids, object_idss, ann_ids, out, superpoints,
            gt_pmasks, gt_spmasks, fps_seed_sp,
        )
        assert len(ann_ids) == 1 and len(scan_ids) == 1
        assert "query" in capture and "inst_feats" in capture

        for i, ann_id in enumerate(ann_ids):
            mask_logits = capture["mask_logits"][i]
            indis_logits = capture["indis_logits"][i]
            quality_scores = capture["quality_scores"][i, :, 0]
            candidate_ious = torch.stack(
                [get_iou(mask, gt_spmasks[i]) for mask in mask_logits]
            )
            oracle_index = int(candidate_ious.argmax())
            indis_index = int(indis_logits.softmax(-1)[:, 1].argmax())
            quality_index = int(quality_scores.argmax())
            identity = dict(
                scene_id=scan_ids[0],
                object_id=str(object_idss[i][0]),
                ann_id=str(ann_id),
            )
            assert key(identity) == key(chosen[len(rows)])
            artifact = f"{scan_ids[0]}_{object_idss[i][0]}_{ann_id}.pth"
            cpu = {
                "mask_logits": mask_logits.to(torch.float16).cpu(),
                "indis_logits": indis_logits.to(torch.float16).cpu(),
                "quality_scores": quality_scores.to(torch.float16).cpu(),
                "proj_query": capture["proj_query"][i].to(torch.float16).cpu(),
                "proj_token": capture["proj_token"][i].to(torch.float16).cpu(),
                "query": capture["query"][i].to(torch.float16).cpu(),
                "query_in": capture["query_in"][i].to(torch.float16).cpu(),
                "inst_feats": capture["inst_feats"][i].to(torch.float16).cpu(),
                "lang_feats": capture["lang_feats"][i].to(torch.float16).cpu(),
                "lang_masks": capture["lang_masks"][i].to(torch.bool).cpu(),
                "batch_mask": capture["batch_mask"][i].to(torch.bool).cpu(),
                "superpoints": superpoints.cpu(),
                "gt_spmask": gt_spmasks[i].to(torch.bool).cpu(),
                "seed_indices": fps_seed_sp[i].cpu(),
                "sample_indices": out["sample_inds"][i].cpu(),
            }
            torch.save(dict(identity=identity, tensors=cpu), output / artifact)
            row = dict(
                **identity,
                candidate_count=int(mask_logits.shape[0]),
                superpoint_count=int(mask_logits.shape[1]),
                oracle_index=oracle_index,
                oracle_iou=float(candidate_ious[oracle_index]),
                indis_index=indis_index,
                indis_iou=float(candidate_ious[indis_index]),
                indis_oracle_rank=rank_of(oracle_index, indis_logits[:, 1].float().tolist()),
                quality_index=quality_index,
                quality_iou=float(candidate_ious[quality_index]),
                quality_oracle_rank=rank_of(oracle_index, quality_scores.float().tolist()),
                artifact=artifact,
                artifact_sha256=sha(output / artifact),
            )
            rows.append(row)
            print(json.dumps(row), flush=True)
        return result

    model.predict_by_feat = capture_predict
    start = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    for index in range(len(dataset)):
        assert time.monotonic() - start < 900, "Capture time budget exceeded"
        free, _ = torch.cuda.mem_get_info()
        assert free >= 5 * 1024**3, "Shared memory headroom dropped"
        batch = dataset.collate_fn([dataset[index]])
        with torch.no_grad():
            result = model(batch, mode="predict")
        del batch, result
        if (index + 1) % 4 == 0:
            print(f"CAPTURED {len(rows)} of {len(chosen)}", flush=True)

    handle_pre.remove()
    handle_post.remove()
    assert len(rows) == len(chosen)
    summary = {
        "status": "complete",
        "checkpoint_sha256": audit["checkpoint_sha256"],
        "module": audit["explicit_module"],
        "audit_sha256": sha(args.audit),
        "manifest_sha256": sha(args.manifest),
        "worker_sha256": sha(__file__),
        "selected_scenes": scenes,
        "descriptions": len(rows),
        "rows": rows,
        "elapsed_seconds": time.monotonic() - start,
        "peak_allocated_mib": torch.cuda.max_memory_allocated() / 1024**2,
        "peak_reserved_mib": torch.cuda.max_memory_reserved() / 1024**2,
        "limitation": (
            "Read-only frozen-checkpoint capture. Candidate evidence tests are "
            "offline diagnostics and do not establish training-time causality."
        ),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("EVIDENCE_CAPTURE_COMPLETE", output, flush=True)


if __name__ == "__main__":
    main()
