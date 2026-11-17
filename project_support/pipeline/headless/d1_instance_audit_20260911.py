"""CPU-only instance attribution of immutable diagnostic banks."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import resource
import time

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "1"
import numpy as np
import torch
from d1_candidate_bank_20260911 import MANIFEST_SHA, key, sha


def mask_stats(pred, target, instances, semantics, target_id):
    pred, target = np.asarray(pred, bool), np.asarray(target, bool)
    assert pred.shape == target.shape == instances.shape == semantics.shape
    assert np.array_equal(target, instances == target_id) and target.any()
    tp = int((pred & target).sum())
    fp = int((pred & ~target).sum())
    fn = int((~pred & target).sum())
    ids, totals = np.unique(instances[instances >= 0], return_counts=True)
    hits = np.array([int((pred & (instances == i)).sum()) for i in ids])
    ious = hits / (pred.sum() + totals - hits + 1e-6)
    best = int(ious.argmax())
    winner = int(ids[best])
    target_sem = np.unique(semantics[target])
    target_semantic = int(target_sem[0]) if len(target_sem) == 1 and target_sem[0] >= 0 else None
    sem_by_id = {}
    for i in ids:
        values = np.unique(semantics[instances == i])
        sem_by_id[int(i)] = int(values[0]) if len(values) == 1 and values[0] >= 0 else None
    target_iou = tp / (tp + fp + fn + 1e-6)
    if not pred.any():
        label = "empty_prediction"
    elif target_iou > .5:
        label = "target_pass50"
    elif float(ious[best]) > .5 and winner != target_id:
        label = ("wrong_instance_same_semantic" if target_semantic is not None and
                 sem_by_id[winner] == target_semantic else
                 "wrong_instance_different_semantic" if target_semantic is not None and
                 sem_by_id[winner] is not None else "wrong_instance_semantic_unknown")
    else:
        label = "no_instance_pass50"
    return dict(label=label, tp=tp, fp=fp, fn=fn, pred_points=int(pred.sum()),
                target_points=int(target.sum()), iou=target_iou,
                precision=tp / (tp + fp) if tp + fp else None,
                recall=tp / (tp + fn), fp_over_target=fp / int(target.sum()),
                fn_over_target=fn / int(target.sum()),
                best_instance=winner if pred.any() else None,
                best_instance_iou=float(ious[best]) if pred.any() else 0.,
                target_semantic=target_semantic,
                best_instance_semantic=sem_by_id[winner] if pred.any() else None,
                same_semantic_other_instances=sum(i != target_id and v == target_semantic
                                                  for i, v in sem_by_id.items())
                if target_semantic is not None else None,
                tied_best_instances=[int(i) for i, v in zip(ids, ious) if v == ious[best]]
                if pred.any() else [],
                unlabelled_pred_points=int((pred & (instances < 0)).sum()))


def main():
    p = argparse.ArgumentParser()
    for name in ("banks", "data-root", "manifest", "out"):
        p.add_argument("--" + name, required=True)
    args = p.parse_args()
    root, data, output = Path(args.banks), Path(args.data_root), Path(args.out)
    assert not output.exists() and sha(args.manifest) == MANIFEST_SHA
    manifest = json.loads(Path(args.manifest).read_text())
    selected = {key(r) for r in manifest["samples"] if r["subset"] == "diagnostic"}
    assert len(selected) == 284
    source = data / "scanrefer/ScanRefer_val_new.json"
    assert sha(source) == manifest["source_sha256"]
    records = {key(r): r for r in json.loads(source.read_text())}
    graph_path = data / "scanrefer/scene_graphs_new_val.json"
    graphs = json.loads(graph_path.read_text())
    torch.set_num_threads(1)
    summaries = {n: json.loads((root / n / "summary.json").read_text()) for n in ("baseline", "m95")}
    assert all({key(r) for r in s["rows"]} == selected for s in summaries.values())
    graph_sha = sha(graph_path)
    assert all(graph_sha == s["scene_graph_sha256"] for s in summaries.values())
    started = time.monotonic()
    rows, scene_checks = [], []
    for scene in sorted({k[0] for k in selected}):
        assert time.monotonic() - started < 600
        path = data / "scannetv2/val" / f"{scene}_refer.pth"
        digest = sha(path)
        assert all(s["input_hashes"][str(path.relative_to(data))] == digest for s in summaries.values())
        xyz, rgb, original_sp, semantic, instance = torch.load(path, map_location="cpu", weights_only=False)
        _, mapping = np.unique(original_sp, return_inverse=True)
        assert len(instance) == len(mapping)
        scene_checks.append(dict(scene_id=scene, sha256=digest, points=len(instance),
                                 object_ids=[int(v) for v in np.unique(instance) if v >= 0]))
        for name, summary in summaries.items():
            for row in summary["rows"]:
                if row["scene_id"] != scene:
                    continue
                path = root / name / row["artifact"]
                assert sha(path) == row["artifact_sha256"]
                bank = torch.load(path, map_location="cpu", weights_only=False)
                assert key(bank["identity"]) == key(row)
                assert np.array_equal(bank["superpoints"].numpy(), mapping)
                target = bank["gt_pmask"].numpy() > .5
                assert np.array_equal(target, instance == int(row["object_id"]))
                result = dict(model=name, **bank["identity"], bank_sha256=row["artifact_sha256"],
                              description=records[key(row)]["description"],
                              object_name=records[key(row)]["object_name"],
                              selected_iou=row["selected_iou"], oracle_iou=row["oracle_iou"],
                              selection_gap=row["selection_gap"])
                for which in ("selected", "oracle"):
                    mask = bank["mask_logits"][row[which + "_index"]].sigmoid().numpy()[mapping] >= .5
                    result[which] = mask_stats(mask, target, instance, semantic, int(row["object_id"]))
                    assert abs(result[which]["iou"] - row[which + "_iou"]) < 1e-7
                    if which == "selected":
                        assert np.array_equal(mask, bank["selected_probabilities"].numpy() >= .5)
                graph = graphs.get(scene, {}).get(row["ann_id"])
                result["parser_graph"] = graph
                result["parser_has_relation_edge"] = bool(graph.get("graph_edge")) if graph is not None else None
                result["relation_failure_label"] = "unknown_not_grounded"
                result["boundary_cause_label"] = "unknown_geometry_not_adjudicated"
                rows.append(result)
        print("SCENE", scene, "rows", len(rows), flush=True)
    assert len(rows) == 568 and not torch.cuda.is_initialized()
    aggregate = {}
    for name in summaries:
        rs = [r for r in rows if r["model"] == name]
        recoverable = [r for r in rs if r["selected_iou"] <= .5 < r["oracle_iou"]]
        aggregate[name] = dict(n=len(rs), selected_labels=dict(Counter(r["selected"]["label"] for r in rs)),
                               recoverable_n=len(recoverable),
                               recoverable_labels=dict(Counter(r["selected"]["label"] for r in recoverable)),
                               oracle_labels=dict(Counter(r["oracle"]["label"] for r in rs)),
                               graph_missing=sum(r["parser_graph"] is None for r in rs),
                               semantic_unknown=sum(r["selected"]["target_semantic"] is None for r in rs))
    output.mkdir(parents=True)
    result = dict(status="complete", worker_sha256=sha(__file__), manifest_sha256=MANIFEST_SHA,
                  source_sha256=sha(source), graph_sha256=sha(graph_path),
                  upstream_summary_hashes={n: sha(root / n / "summary.json") for n in summaries},
                  cuda_initialized=False, rows=rows, aggregate=aggregate, scene_checks=scene_checks,
                  elapsed_seconds=time.monotonic() - started,
                  peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                  limitations="Instance overlap is descriptive, not causal attribution. Semantic IDs are coarse categories. Parser edges are not grounded relation labels. No boundary/anchor-error adjudication, new inference or reserved-scene analysis.")
    (output / "instance_audit.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(aggregate, indent=2), flush=True)


if __name__ == "__main__":
    main()
