"""Isolated fixed-checkpoint diagnostic pilot; no training/package mutations."""
import argparse
import gc
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time
import types

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

MANIFEST_SHA = "84a7d60f85ecd5bec44b77b304140ff00c8c1fa00177dc12ecf7ef5ebfabb468"
BUFFER_KEYS = {
    "text_encoder.embeddings.position_ids",
    "text_encoder.embeddings.token_type_ids",
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def key(record):
    return (record["scene_id"], str(record["object_id"]), str(record["ann_id"]))


def bank_metrics(logits, scores, mapping, gt, get_iou):
    import torch
    assert logits.ndim == 2 and logits.shape[0] > 0
    assert scores.shape == (logits.shape[0], 2)
    assert mapping.ndim == 1 and mapping.numel() == gt.numel()
    assert mapping.min() >= 0 and mapping.max() < logits.shape[1]
    assert torch.isfinite(logits).all() and torch.isfinite(scores).all()
    selected = int(scores.softmax(-1)[:, 1].argmax())
    # Evaluate one proposal at a time: O(N) temporary storage, not a Q-by-N bank.
    ious = torch.stack([get_iou(mask[mapping], gt) for mask in logits])
    assert torch.isfinite(ious).all()
    a, o = float(ious[selected]), float(ious.max())
    assert o >= a and abs((1 - a) - ((1 - o) + (o - a))) < 1e-12
    return dict(selected_index=selected, oracle_index=int(ious.argmax()),
                selected_iou=a, oracle_iou=o, bank_limitation=1 - o,
                selection_gap=o - a, candidate_ious=ious.tolist())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-root", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--scene-limit", type=int, default=2)
    args = parser.parse_args()
    root, output = Path(args.code_root), Path(args.out)
    assert args.scene_limit > 0
    assert not output.exists(), "Immutable output directory already exists"
    assert sha(args.manifest) == MANIFEST_SHA
    audit = json.loads(Path(args.audit).read_text())
    assert sha(audit["checkpoint"]) == audit["checkpoint_sha256"]
    assert sha(audit["config"]) == audit["config_sha256"]
    assert subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip() == audit["code_head"]
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import gorilla
    import torch
    from framework.dataset import build_dataset

    torch.set_num_threads(1)
    free, total = torch.cuda.mem_get_info()
    assert free >= 8 * 1024**3, f"Insufficient preflight free memory: {free}"
    # A bounded eval worker may not consume the trainers' remaining headroom.
    torch.cuda.set_per_process_memory_fraction(4 * 1024**3 / total)
    gorilla.set_random_seed(1999)
    cfg = gorilla.Config.fromfile(audit["config"])
    assert cfg.test.seed == 1999
    assert not cfg.data.val.training and cfg.data.val.get("src_sample", -1) == -1
    data_root = Path(cfg.data.val.data_root)
    source = data_root / "scanrefer/ScanRefer_val_new.json"
    manifest = json.loads(Path(args.manifest).read_text())
    assert sha(source) == manifest["source_sha256"]
    assert (data_root / "scanrefer/scene_graphs_new_val.json").is_file()
    records = json.loads(source.read_text())
    by_key = {key(record): record for record in records}
    assert len(by_key) == len(records)
    samples = [s for s in manifest["samples"] if s["subset"] == "diagnostic"]
    scenes = sorted({s["scene_id"] for s in samples})[:args.scene_limit]
    chosen = [s for s in samples if s["scene_id"] in scenes]
    assert len(chosen) == 4 * len(scenes)
    output.mkdir(parents=True)
    logger = logging.getLogger("d1")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    dataset = build_dataset(cfg.data.val, logger)
    # A singleton pilot reduces sharing impact; it is NOT a full historical replay.
    dataset.scene_inputs = [[by_key[key(s)]] for s in chosen]
    module = importlib.import_module(audit["explicit_module"])
    package = Path(module.__file__).parent
    assert {p.name: sha(p) for p in sorted(package.glob("*.py"))} == audit["package_sha256"]
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
    model.load_state_dict({k: v for k, v in state.items() if k not in BUFFER_KEYS}, strict=True)
    del state, checkpoint, expected
    gc.collect()
    model.cuda().eval()
    original = model.predict_by_feat
    rows = []

    def capture(self, scan_ids, object_idss, ann_ids, out, superpoints,
                gt_pmasks, gt_spmasks, fps_seed_sp):
        result = original(scan_ids, object_idss, ann_ids, out, superpoints,
                          gt_pmasks, gt_spmasks, fps_seed_sp)
        assert len(ann_ids) == 1 and len(scan_ids) == 1
        for i, ann_id in enumerate(ann_ids):
            logits = out["masks"][i].detach()
            scores = out["indis"][i].detach()
            metrics = bank_metrics(logits, scores, superpoints, gt_pmasks[i], get_iou)
            selected = metrics["selected_index"]
            expected_probs = logits[selected][superpoints].sigmoid().cpu()
            assert torch.equal(expected_probs, result["pred_pmask"][i])
            assert metrics["selected_iou"] == float(result["piou"][i])
            cpu = dict(mask_logits=logits.cpu(), score_logits=scores.cpu(),
                       superpoints=superpoints.cpu(), gt_pmask=gt_pmasks[i].cpu(),
                       gt_spmask=gt_spmasks[i].cpu(),
                       selected_probabilities=result["pred_pmask"][i],
                       seed_indices=fps_seed_sp[i].cpu(),
                       sample_indices=out["sample_inds"][i].cpu())
            assert len(object_idss[i]) == 1
            identity = dict(scene_id=scan_ids[0], object_id=str(object_idss[i][0]),
                            ann_id=str(ann_id))
            assert key(identity) == key(chosen[len(rows)])
            artifact = f"{scan_ids[0]}_{object_idss[i][0]}_{ann_id}.pth"
            torch.save(dict(identity=identity, metrics=metrics, **cpu), output / artifact)
            row = dict(**identity, **metrics, candidate_count=logits.shape[0],
                       superpoint_count=logits.shape[1], point_count=superpoints.numel(),
                       gt_points=int((gt_pmasks[i] > .5).sum()),
                       selected_sp_iou=float(result["spiou"][i]),
                       artifact=artifact, artifact_sha256=sha(output / artifact),
                       original_prediction_equal=True)
            rows.append(row)
            print(json.dumps(row), flush=True)
        return result

    model.predict_by_feat = types.MethodType(capture, model)
    start = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    for index in range(len(dataset)):
        assert time.monotonic() - start < 600, "Pilot time budget exceeded"
        free, _ = torch.cuda.mem_get_info()
        assert free >= 5 * 1024**3, "Shared memory headroom dropped"
        batch = dataset.collate_fn([dataset[index]])
        with torch.no_grad():
            result = model(batch, mode="predict")
        del batch, result
    assert len(rows) == len(chosen)
    summary = dict(
        status="pilot_complete", checkpoint_sha256=audit["checkpoint_sha256"],
        module=audit["explicit_module"], audit_sha256=sha(args.audit),
        manifest_sha256=sha(args.manifest), worker_sha256=sha(__file__),
        source_sha256=sha(source), selected_scenes=scenes, descriptions=len(rows),
        protocol="First two lexicographic diagnostic scenes; all four frozen descriptions; singleton language batches",
        historical_replay_verified=False, inference_only=True,
        threshold="sigmoid(logit) >= 0.5; GT > 0.5; union+1e-6",
        input_hashes={str(p.relative_to(data_root)): sha(p) for scene in scenes for p in (
            data_root / "scannetv2/val" / f"{scene}_refer.pth",
            data_root / "clip_feat" / f"{scene}.pth")},
        scene_graph_sha256=sha(data_root / "scanrefer/scene_graphs_new_val.json"),
        peak_allocated_mib=torch.cuda.max_memory_allocated() / 1024**2,
        peak_reserved_mib=torch.cuda.max_memory_reserved() / 1024**2,
        elapsed_seconds=time.monotonic() - start, rows=rows,
        limitation="Correctness pilot only, not representative error prevalence or untouched evaluation. Singleton padding/grouping and historical forward identity remain unverified.")
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("PILOT_COMPLETE", output, flush=True)


if __name__ == "__main__":
    main()
