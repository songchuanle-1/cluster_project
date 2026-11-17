"""Scene-level uncertainty for the corrected selection metrics.

The111052 audit requires same-class controls with scene-level uncertainty, because
expressions repeat scenes and per-expression counts are not independent samples. This
re-uses the single same-forward capture from acceptable_mask_rank_20260916.json and
reports scene-balanced rates with a scene-level bootstrap.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path("D:/project/cluster_project")
SOURCE = ROOT / "pipeline/reports/acceptable_mask_rank_20260916.json"
OUT = ROOT / "pipeline/reports/selection_scene_uncertainty_20260916.json"
SEED = 1999
DRAWS = 10000


def bootstrap(scene_rates, draws=DRAWS, seed=SEED):
    rng = np.random.RandomState(seed)
    values = np.asarray(scene_rates, dtype=float)
    n = len(values)
    samples = values[rng.randint(0, n, size=(draws, n))].mean(axis=1)
    return dict(mean=float(samples.mean()),
                lo=float(np.percentile(samples, 2.5)),
                hi=float(np.percentile(samples, 97.5)),
                draws=draws, seed=seed)


def main():
    data = json.loads(SOURCE.read_text())
    rows = data["rows"]
    by_scene = defaultdict(list)
    for r in rows:
        by_scene[r["scene"]].append(r)

    def rate(group, key):
        return sum(1 for r in group if r[key]) / len(group)

    per_scene = {}
    for scene, group in by_scene.items():
        has_acc = [r for r in group if r["n_acceptable"] > 0]
        ranks = [r["best_acceptable_rank"] for r in has_acc]
        per_scene[scene] = dict(
            n=len(group),
            success=rate(group, "success"),
            has_acceptable_mask=(len(has_acc) / len(group)),
            has_acceptable_any_given=len(has_acc) > 0,
            best_rank_top5=(
                sum(1 for v in ranks if v <= 5) / len(ranks) if ranks else None),
            best_rank_median=(sorted(ranks)[len(ranks) // 2] if ranks else None),
            mean_acceptable=(sum(r["n_acceptable"] for r in group) / len(group)),
            false_positive_on_unacceptable=(
                sum(1 for r in group if not r["success"] and r["n_acceptable"] > 0)
                / len(group)))

    scenes = list(per_scene)
    metrics = {
        "success": [per_scene[s]["success"] for s in scenes],
        "has_acceptable_mask": [per_scene[s]["has_acceptable_mask"]
                                for s in scenes],
        "best_rank_top5": [per_scene[s]["best_rank_top5"] for s in scenes
                           if per_scene[s]["best_rank_top5"] is not None],
        "false_positive_on_unacceptable": [
            per_scene[s]["false_positive_on_unacceptable"] for s in scenes],
    }
    summary = {
        "expressions": len(rows),
        "scenes": len(scenes),
        "expressions_per_scene_histogram": {
            str(k): sum(1 for g in by_scene.values() if len(g) == k)
            for k in sorted({len(g) for g in by_scene.values()})},
        "pooled": {
            "success": sum(1 for r in rows if r["success"]) / len(rows),
            "has_acceptable_mask": (
                sum(1 for r in rows if r["n_acceptable"] > 0) / len(rows)),
            "false_positive_on_unacceptable": (
                sum(1 for r in rows
                    if not r["success"] and r["n_acceptable"] > 0) / len(rows)),
            "best_rank_top5": (
                sum(1 for r in rows if r["best_acceptable_rank"] and
                    r["best_acceptable_rank"] <= 5)
                / max(sum(1 for r in rows if r["n_acceptable"] > 0), 1)),
        },
        "scene_balanced": {k: float(np.mean(v)) for k, v in metrics.items()},
        "scene_bootstrap_95ci": {k: bootstrap(v) for k, v in metrics.items()},
        "scenes_with_no_acceptable_mask": sum(
            1 for s in scenes
            if not per_scene[s]["has_acceptable_any_given"]),
        "dependency_note": (
            "Expressions repeat scenes (30 scenes have 4, one has 1, one has 2). "
            "Pooled rates over expressions therefore over-weight repeated scenes; "
            "the scene-balanced and bootstrap figures are the ones to cite."),
    }
    report = dict(
        summary=summary, per_scene=per_scene,
        scope="Derived entirely from the single same-forward capture in "
              "acceptable_mask_rank_20260916.json; no new model run and no "
              "cross-capture join. Scene-level bootstrap resamples SCENES with "
              "replacement, 10000 draws, seed1999, so intervals reflect scene "
              "clustering rather than expression count. Diagnosis only.",
        sources={str(SOURCE): hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                 str(Path(__file__)): hashlib.sha256(
                     Path(__file__).read_bytes()).hexdigest()})
    OUT.write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
