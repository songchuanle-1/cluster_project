"""Bounded original-group capture of fixed evaluation semantic projections."""
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

from d1_candidate_bank_20260911 import BUFFER_KEYS, MANIFEST_SHA, key, sha


def main():
    ap = argparse.ArgumentParser()
    for name in ("code-root", "audit", "manifest", "protocol", "out"):
        ap.add_argument("--" + name, required=True)
    args = ap.parse_args()
    root, output = Path(args.code_root), Path(args.out)
    assert not output.exists()
    protocol = json.loads(Path(args.protocol).read_text())
    audit = json.loads(Path(args.audit).read_text())
    assert sha(args.manifest) == MANIFEST_SHA == protocol["manifest_sha256"]
    for field in ("checkpoint", "config"):
        assert sha(audit[field]) == audit[field + "_sha256"]
    for rel, digest in protocol["source_hashes"].items():
        assert sha(root / rel) == digest
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
    selected = {tuple(k) for k in protocol["ids"]}
    manifest = json.loads(Path(args.manifest).read_text())
    assert selected <= {key(r) for r in manifest["samples"] if r["subset"] == "diagnostic"}
    data = Path(cfg.data.val.data_root)
    assert sha(data / "scanrefer/ScanRefer_val_new.json") == manifest["source_sha256"]
    scenes = sorted({k[0] for k in selected})
    input_hashes = {str(p.relative_to(data)): sha(p) for scene in scenes for p in (
        data / "scannetv2/val" / f"{scene}_refer.pth", data / "clip_feat" / f"{scene}.pth")}
    logger = logging.getLogger("padding_capture")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    dataset = build_dataset(cfg.data.val, logger)
    groups = [g for g in dataset.scene_inputs if any(key(r) in selected for r in g)]
    members = [key(r) for g in groups for r in g if key(r) in selected]
    assert len(members) == len(set(members)) == 21 and set(members) == selected
    module = importlib.import_module(audit["explicit_module"])
    package = Path(module.__file__).parent
    assert {p.name: sha(p) for p in sorted(package.glob("*.py"))} == audit["package_sha256"]
    model = module.Network(**cfg.model)
    state = torch.load(audit["checkpoint"], map_location="cpu", weights_only=False)["model"]
    expected = model.state_dict()
    assert set(state) - set(expected) == BUFFER_KEYS and not set(expected) - set(state)
    for k in BUFFER_KEYS:
        assert torch.equal(state[k], getattr(model.text_encoder.embeddings, k.rsplit(".", 1)[1]))
    model.load_state_dict({k: v for k, v in state.items() if k not in BUFFER_KEYS}, strict=True)
    del state, expected
    gc.collect()
    model.cuda().eval()
    original = model.predict_by_feat
    captured = {}
    batch = None

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
            captured[identity] = dict(
                identity=dict(scene_id=identity[0], object_id=identity[1], ann_id=identity[2]),
                proj_queries=out["proj_queries"][i].detach().cpu(),
                proj_tokens=out["proj_tokens"][i].detach().cpu(),
                lang_masks=batch["lang_masks"][i].detach().cpu(),
                token_ids=batch["lang_tokenss"][i].detach().cpu(),
                dense_maps={k: v.detach().cpu() for k, v in batch["dense_maps"][i].items()},
                mask_logits=out["masks"][i].detach().cpu(),
                score_logits=out["indis"][i].detach().cpu(),
                seed_indices=fps_seed_sp[i].detach().cpu(),
                sample_indices=out["sample_inds"][i].detach().cpu(),
                superpoints=superpoints.detach().cpu(), gt_pmask=gt_pmasks[i].detach().cpu(),
                gt_spmask=gt_spmasks[i].detach().cpu(),
                selected_iou=float(result["piou"][i]))
        return result

    model.predict_by_feat = types.MethodType(capture, model)
    output.mkdir(parents=True)
    started = time.monotonic()
    rows, records = [], []
    torch.cuda.reset_peak_memory_stats()
    summary = dict(protocol_sha256=sha(args.protocol), worker_sha256=sha(__file__),
                   audit_sha256=sha(args.audit), checkpoint_sha256=audit["checkpoint_sha256"],
                   config_sha256=audit["config_sha256"], input_hashes=input_hashes,
                   scene_graph_sha256=sha(data / "scanrefer/scene_graphs_new_val.json"),
                   temperature=model.criterion.temperature, eos_coef=model.criterion.eos_coef,
                   original_lang_num_max=cfg.data.val.lang_num_max,
                   inference_only=True, historical_replay_verified=False)

    def persist(status):
        done = {key(r) for r in rows}
        summary.update(status=status, rows=rows, groups=records,
                       missing_ids=[list(k) for k in sorted(selected - done)],
                       elapsed_seconds=time.monotonic() - started,
                       peak_allocated_mib=torch.cuda.max_memory_allocated() / 1024**2,
                       peak_reserved_mib=torch.cuda.max_memory_reserved() / 1024**2)
        (output / "summary.json").write_text(json.dumps(summary, indent=2))

    persist("running")
    for index, group in enumerate(groups):
        wanted = {key(r) for r in group if key(r) in selected}
        record = dict(index=index, members=[list(key(r)) for r in group],
                      diagnostic_members=[list(k) for k in sorted(wanted)])
        records.append(record)
        free, _ = torch.cuda.mem_get_info()
        reason = ("time_budget" if time.monotonic() - started >= 300 else
                  "free_memory_guard" if free < 5 * 1024**3 else None)
        if reason:
            record.update(status="skipped", reason=reason, free_bytes=free)
            persist("running")
            continue
        captured.clear()
        dataset.scene_inputs = [group]
        try:
            batch = dataset.collate_fn([dataset[0]])
            with torch.no_grad():
                model(batch, mode="predict")
            assert set(captured) == wanted
        except torch.cuda.OutOfMemoryError as error:
            record.update(status="skipped", reason="allocator_cap_oom", error=str(error))
        else:
            for identity, item in sorted(captured.items()):
                filename = "_".join(identity) + ".pth"
                torch.save(item, output / filename)
                rows.append(dict(**item["identity"], group_index=index, artifact=filename,
                                 artifact_sha256=sha(output / filename)))
            record["status"] = "complete"
        finally:
            batch = None
            captured.clear()
            gc.collect()
            torch.cuda.empty_cache()
        persist("running")
        print("GROUP", index, record["status"], "captured", len(rows), flush=True)
    persist("complete" if len(rows) == len(selected) else "partial")
    print("CAPTURE_FINISHED", summary["status"], len(rows), flush=True)


if __name__ == "__main__":
    main()
