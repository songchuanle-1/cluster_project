"""Frozen full diagnostic sample, original groups, bounded shared-GPU inference."""
import argparse
import gc
import importlib
import json
import logging
from pathlib import Path
import subprocess
import sys
import time
import types

from d1_candidate_bank_20260911 import BUFFER_KEYS, MANIFEST_SHA, bank_metrics, key, sha


def main():
    parser = argparse.ArgumentParser()
    for arg in ("code-root", "audit", "manifest", "out"):
        parser.add_argument("--" + arg, required=True)
    args = parser.parse_args()
    root, output = Path(args.code_root), Path(args.out)
    assert not output.exists()
    assert sha(args.manifest) == MANIFEST_SHA
    audit = json.loads(Path(args.audit).read_text())
    for field in ("checkpoint", "config"):
        assert sha(audit[field]) == audit[field + "_sha256"]
    assert subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                   text=True).strip() == audit["code_head"]
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import gorilla
    import torch
    from framework.dataset import build_dataset

    torch.set_num_threads(1)
    free, total = torch.cuda.mem_get_info()
    assert free >= 8 * 1024**3
    torch.cuda.set_per_process_memory_fraction(4 * 1024**3 / total)
    gorilla.set_random_seed(1999)
    cfg = gorilla.Config.fromfile(audit["config"])
    assert cfg.test.seed == 1999 and not cfg.data.val.training
    assert cfg.data.val.get("src_sample", -1) == -1
    manifest = json.loads(Path(args.manifest).read_text())
    data_root = Path(cfg.data.val.data_root)
    assert sha(data_root / "scanrefer/ScanRefer_val_new.json") == manifest["source_sha256"]
    selected = {key(r): r for r in manifest["samples"] if r["subset"] == "diagnostic"}
    scenes = sorted({r["scene_id"] for r in selected.values()})
    assert len(selected) == 284 and len(scenes) == 71
    input_hashes = {str(p.relative_to(data_root)): sha(p) for scene in scenes for p in (
        data_root / "scannetv2/val" / f"{scene}_refer.pth",
        data_root / "clip_feat" / f"{scene}.pth")}
    logger = logging.getLogger("d1_expansion")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    dataset = build_dataset(cfg.data.val, logger)
    groups = [g for g in dataset.scene_inputs if any(key(r) in selected for r in g)]
    assert all(all(r["scene_id"] in scenes for r in g) for g in groups)
    grouped_ids = [key(r) for g in groups for r in g if key(r) in selected]
    assert len(grouped_ids) == len(set(grouped_ids)) == len(selected)
    assert set(grouped_ids) == set(selected)
    module = importlib.import_module(audit["explicit_module"])
    package = Path(module.__file__).parent
    assert {p.name: sha(p) for p in sorted(package.glob("*.py"))} == audit["package_sha256"]
    get_iou = importlib.import_module(audit["explicit_module"] + ".loss").get_iou
    model = module.Network(**cfg.model)
    assert model.task_type == "res"
    state = torch.load(audit["checkpoint"], map_location="cpu", weights_only=False)["model"]
    expected = model.state_dict()
    assert set(state) - set(expected) == BUFFER_KEYS
    assert not set(expected) - set(state)
    for k in BUFFER_KEYS:
        assert torch.equal(state[k], getattr(model.text_encoder.embeddings, k.rsplit(".", 1)[1]))
    model.load_state_dict({k: v for k, v in state.items() if k not in BUFFER_KEYS}, strict=True)
    del state, expected
    gc.collect()
    model.cuda().eval()
    original = model.predict_by_feat
    captured = {}

    def capture(self, scan_ids, object_idss, ann_ids, out, superpoints,
                gt_pmasks, gt_spmasks, fps_seed_sp):
        result = original(scan_ids, object_idss, ann_ids, out, superpoints,
                          gt_pmasks, gt_spmasks, fps_seed_sp)
        assert len(scan_ids) == 1
        for i, ann in enumerate(ann_ids):
            assert len(object_idss[i]) == 1
            identity = (scan_ids[0], str(object_idss[i][0]), str(ann))
            if identity not in selected:
                continue
            assert identity not in captured
            logits, scores = out["masks"][i].detach(), out["indis"][i].detach()
            metrics = bank_metrics(logits, scores, superpoints, gt_pmasks[i], get_iou)
            assert torch.equal(logits[metrics["selected_index"]][superpoints].sigmoid().cpu(),
                               result["pred_pmask"][i])
            assert float(result["piou"][i]) == metrics["selected_iou"]
            captured[identity] = dict(
                identity=dict(scene_id=identity[0], object_id=identity[1], ann_id=identity[2]),
                mask_logits=logits.cpu(), score_logits=scores.cpu(),
                selected_probabilities=result["pred_pmask"][i],
                superpoints=superpoints.cpu(), gt_pmask=gt_pmasks[i].cpu(),
                gt_spmask=gt_spmasks[i].cpu(), seed_indices=fps_seed_sp[i].cpu(),
                sample_indices=out["sample_inds"][i].cpu(), metrics=metrics)
        return result

    model.predict_by_feat = types.MethodType(capture, model)
    output.mkdir(parents=True)
    started = time.monotonic()
    rows, group_records = [], []
    torch.cuda.reset_peak_memory_stats()
    summary = dict(
        status="running", checkpoint_sha256=audit["checkpoint_sha256"],
        module=audit["explicit_module"], audit_sha256=sha(args.audit),
        manifest_sha256=sha(args.manifest), worker_sha256=sha(__file__),
        helper_sha256=sha(Path(__file__).with_name("d1_candidate_bank_20260911.py")),
        source_sha256=manifest["source_sha256"], selected_scenes=scenes,
        expected_ids=[list(k) for k in sorted(selected)], input_hashes=input_hashes,
        scene_graph_sha256=sha(data_root / "scanrefer/scene_graphs_new_val.json"),
        original_lang_num_max=cfg.data.val.lang_num_max,
        threshold="sigmoid(logit)>=0.5; GT>0.5; union+1e-6",
        protocol="All284 frozen diagnostic IDs in original saved-config language groups",
        historical_replay_verified=False, inference_only=True,
        limitation="Exploratory equal-scene diagnostic sample; reserved scenes never inferred. Context descriptions are not scored observations. No causal, novelty or deployable oracle claim.")

    def persist(status):
        done = {key(r) for r in rows}
        summary.update(status=status, rows=rows, groups=group_records,
                       descriptions=len(rows), missing_ids=[list(k) for k in sorted(set(selected) - done)],
                       elapsed_seconds=time.monotonic() - started,
                       peak_allocated_mib=torch.cuda.max_memory_allocated() / 1024**2,
                       peak_reserved_mib=torch.cuda.max_memory_reserved() / 1024**2)
        (output / "summary.json").write_text(json.dumps(summary, indent=2))

    persist("running")
    for index, group in enumerate(groups):
        diagnostic_ids = {key(r) for r in group if key(r) in selected}
        record = dict(index=index, members=[list(key(r)) for r in group],
                      diagnostic_members=[list(k) for k in sorted(diagnostic_ids)])
        group_records.append(record)
        free, _ = torch.cuda.mem_get_info()
        reason = ("time_budget" if time.monotonic() - started >= 600
                  else "free_memory_guard" if free < 5 * 1024**3 else None)
        if reason:
            record.update(status="skipped", reason=reason, free_bytes=free)
            persist("running")
            continue
        captured.clear()
        dataset.scene_inputs = [group]
        batch = None
        try:
            batch = dataset.collate_fn([dataset[0]])
            record["token_length"] = int(batch["lang_tokenss"].shape[1])
            with torch.no_grad():
                model(batch, mode="predict")
            assert set(captured) == diagnostic_ids
        except torch.cuda.OutOfMemoryError as error:
            record.update(status="skipped", reason="allocator_cap_oom", error=str(error))
            captured.clear()
        else:
            for identity in sorted(captured):
                bank = captured[identity]
                filename = "_".join(identity) + ".pth"
                torch.save(bank, output / filename)
                rows.append(dict(**bank["identity"], **bank["metrics"],
                                 group_index=index, group_size=len(group),
                                 candidate_count=bank["mask_logits"].shape[0],
                                 point_count=bank["superpoints"].numel(),
                                 gt_points=int((bank["gt_pmask"] > .5).sum()),
                                 artifact=filename, artifact_sha256=sha(output / filename),
                                 original_prediction_equal=True))
            record["status"] = "complete"
        finally:
            del batch
            captured.clear()
            gc.collect()
            torch.cuda.empty_cache()
        persist("running")
        print("GROUP", index, record["status"], "captured", len(rows), flush=True)
    persist("complete" if len(rows) == len(selected) else "partial")
    print("EXPANSION_FINISHED", summary["status"], len(rows), "of", len(selected), flush=True)


if __name__ == "__main__":
    main()
