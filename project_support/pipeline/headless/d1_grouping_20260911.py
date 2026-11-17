"""Isolated same-checkpoint repeat/padding/original-group diagnostic audit."""
import argparse
import gc
import importlib
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time
import types

from d1_candidate_bank_20260911 import BUFFER_KEYS, MANIFEST_SHA, bank_metrics, key, sha


def compare(left, right):
    import torch
    result = {}
    for field in ("mask_logits", "score_logits", "selected_probabilities"):
        a, b = left[field], right[field]
        assert a.shape == b.shape
        result[field + "_max_abs"] = float((a - b).abs().max())
        result[field + "_exact"] = torch.equal(a, b)
    result["bank_bit_changes"] = int(((left["mask_logits"].sigmoid() >= .5) !=
                                    (right["mask_logits"].sigmoid() >= .5)).sum())
    result["selected_point_bit_changes"] = int(((left["selected_probabilities"] >= .5) !=
                                              (right["selected_probabilities"] >= .5)).sum())
    for field in ("seed_indices", "sample_indices", "superpoints", "gt_pmask"):
        result[field + "_equal"] = torch.equal(left[field], right[field])
    for field in ("selected_iou", "oracle_iou"):
        result[field + "_delta"] = right["metrics"][field] - left["metrics"][field]
    result["selected_index_equal"] = left["metrics"]["selected_index"] == right["metrics"]["selected_index"]
    return result


def main():
    parser = argparse.ArgumentParser()
    for arg in ("code-root", "audit", "manifest", "pilot", "out"):
        parser.add_argument("--" + arg, required=True)
    args = parser.parse_args()
    root, output, pilot = Path(args.code_root), Path(args.out), Path(args.pilot)
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
    import torch.nn.functional as F
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
    old_summary = json.loads((pilot / "summary.json").read_text())
    assert old_summary["checkpoint_sha256"] == audit["checkpoint_sha256"]
    selected = {key(r): r for r in old_summary["rows"]}
    assert len(selected) == 8
    assert set(selected) <= {key(r) for r in manifest["samples"] if r["subset"] == "diagnostic"}
    for relative, digest in old_summary["input_hashes"].items():
        assert sha(data_root / relative) == digest
    assert sha(data_root / "scanrefer/scene_graphs_new_val.json") == old_summary["scene_graph_sha256"]
    logger = logging.getLogger("d1_group")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    dataset = build_dataset(cfg.data.val, logger)
    groups = [g for g in dataset.scene_inputs if any(key(r) in selected for r in g)]
    assert all(g[0]["scene_id"] in old_summary["selected_scenes"] for g in groups)
    assert {key(r) for g in groups for r in g if key(r) in selected} == set(selected)
    module = importlib.import_module(audit["explicit_module"])
    package = Path(module.__file__).parent
    assert {p.name: sha(p) for p in sorted(package.glob("*.py"))} == audit["package_sha256"]
    get_iou = importlib.import_module(audit["explicit_module"] + ".loss").get_iou
    model = module.Network(**cfg.model)
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
            identity = (scan_ids[0], str(object_idss[i][0]), str(ann))
            if identity not in selected:
                continue
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

    def make_batch(records):
        dataset.scene_inputs = [records]
        return dataset.collate_fn([dataset[0]])

    def infer(batch):
        assert time.monotonic() - started < 600
        free, _ = torch.cuda.mem_get_info()
        assert free >= 5 * 1024**3
        captured.clear()
        with torch.no_grad():
            model(batch, mode="predict")
        return dict(captured)

    torch.cuda.reset_peak_memory_stats()
    for group_index, group in enumerate(groups):
        group_batch = make_batch(group)
        length = group_batch["lang_tokenss"].shape[1]
        group_records.append(dict(index=group_index, token_length=length,
                                  members=[list(key(r)) for r in group],
                                  diagnostic_members=[list(key(r)) for r in group if key(r) in selected]))
        singles = {}
        for record in group:
            identity = key(record)
            if identity not in selected:
                continue
            batch = make_batch([record])
            first = infer(batch)[identity]
            second = infer(batch)[identity]
            pad = length - batch["lang_tokenss"].shape[1]
            assert pad >= 0
            batch["lang_tokenss"] = F.pad(batch["lang_tokenss"], (0, pad), value=dataset.tokenizer.pad_token_id)
            batch["lang_masks"] = F.pad(batch["lang_masks"], (0, pad), value=0)
            pos = next(i for i, r in enumerate(group) if key(r) == identity)
            assert torch.equal(batch["lang_tokenss"][0], group_batch["lang_tokenss"][pos])
            assert torch.equal(batch["lang_masks"][0], group_batch["lang_masks"][pos])
            padded = infer(batch)[identity]
            old = selected[identity]
            assert sha(pilot / old["artifact"]) == old["artifact_sha256"]
            old_bank = torch.load(pilot / old["artifact"], map_location="cpu", weights_only=False)
            singles[identity] = (first, padded, dict(
                identity=list(identity), group_index=group_index,
                group_size=len(group), padded_tokens=pad,
                repeat=compare(first, second), padding=compare(first, padded),
                versus_prior_pilot=compare(old_bank, first)))
        grouped = infer(group_batch)
        for identity, (first, padded, row) in singles.items():
            bank = grouped[identity]
            row["batch_effect"] = compare(padded, bank)
            row["total_group_effect"] = compare(first, bank)
            row["grouped_metrics"] = bank["metrics"]
            row["singleton_metrics"] = first["metrics"]
            filename = "_".join(identity) + ".pth"
            torch.save(bank, output / filename)
            row["artifact"], row["artifact_sha256"] = filename, sha(output / filename)
            rows.append(row)
            print(json.dumps({k: v for k, v in row.items()
                              if k not in ("grouped_metrics", "singleton_metrics")}), flush=True)
        del group_batch, grouped, singles
        captured.clear()
        gc.collect()
        torch.cuda.empty_cache()
    assert len(rows) == 8
    result = dict(status="complete", rows=rows, groups=group_records,
                  module=audit["explicit_module"], checkpoint_sha256=audit["checkpoint_sha256"],
                  worker_sha256=sha(__file__), helper_sha256=sha(Path(__file__).with_name("d1_candidate_bank_20260911.py")),
                  pilot_summary_sha256=sha(pilot / "summary.json"), manifest_sha256=sha(args.manifest),
                  original_lang_num_max=cfg.data.val.lang_num_max,
                  peak_allocated_mib=torch.cuda.max_memory_allocated()/1024**2,
                  peak_reserved_mib=torch.cuda.max_memory_reserved()/1024**2,
                  elapsed_seconds=time.monotonic()-started,
                  limitation="Eight fixed examples only. Group nuisance descriptions not diagnostic samples. No historical fullvalidation or causal mechanism claim.")
    (output / "summary.json").write_text(json.dumps(result, indent=2))
    print("GROUP_AUDIT_COMPLETE", len(rows), len(groups), flush=True)


if __name__ == "__main__":
    main()
