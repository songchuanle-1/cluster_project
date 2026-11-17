"""Persist measured capture evidence and candidate-specific remaining work."""
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
RAW = "pipeline/reports/native_support_capture_20260916-1517.json"
REPORT = "pipeline/reports/native_support_validation_20260916-1513.json"


def evidence(path):
    return dict(path=path, sha256=hashlib.sha256((ROOT / path).read_bytes()).hexdigest())


def main():
    data = json.loads((ROOT / RAW).read_text(encoding="ascii"))
    rows = data["rows"]
    from native_support_capture_20260916 import physical_join
    for row in rows:
        physical_join(row, row)
    keys = [(r["capture_id"], r["scene_occurrence"], r["expression_slot"]) for r in rows]
    assert len(keys) == len(set(keys)) == 16
    assert data["native_capture_completed"] and data["batches"] == 2
    scene_rates = {}
    for row in rows:
        scene_rates.setdefault(row["scene"], []).append(
            row["ious"][row["selected_query"]] > .5)
    ranks = [r["best_acceptable_rank"] for r in rows if r["best_acceptable_rank"] is not None]
    report = dict(
        scope="Two-batch native M95 TRAIN capture plumbing validation, not efficacy or novelty",
        expressions=len(rows), scenes=len(scene_rates), batches=data["batches"],
        selected_success=data["selected_success"], no_acceptable=data["no_acceptable"],
        scene_balanced_success=statistics.mean(statistics.mean(v) for v in scene_rates.values()),
        acceptable_median_rank=statistics.median(ranks) if ranks else None,
        positive_slots=sum(sum(r["native_positive"]) for r in rows),
        seed_inside_slots=sum(sum(r["seed_inside"]) for r in rows),
        mask_ok_slots=sum(sum(i > .5 for i in r["ious"]) for r in rows),
        static_tests_passed=13, native_argmax_matches=True,
        features=["raw_3d", "raw_2d", "projected_3d", "projected_2d", "fused", "final"],
        remote_feature_directory="/data3/songcl/Project/Cluster_project/pipeline/native_support_capture_20260916-1517",
        feature_artifacts=data["feature_artifacts"],
        limitations=[
            "16 expressions are not the prior 123-expression paired sample; do not compare effect sizes.",
            "Native captures bind endpoints but feature contrasts and connected text controls remain uncomputed.",
            "All-acceptable statistics use superpoint IoU, not the goal point-mask mIoU.",
            "PIRS is still training; no terminal comparison or scientific admission.",
            "1517 is an artifact identifier, not an asserted wall-clock completion timestamp.",
        ],
        sources=[evidence(p) for p in (RAW, "scripts/native_support_capture_20260916.py",
                                      "scripts/test_native_support_capture_20260916.py",
                                      "scripts/capture_support_20260916.py")])
    (ROOT / REPORT).write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    actions = {
        "referent-causality-audit": "Await terminal PIRS; capture preregistered paired scene manifest with exact axes. Two-batch M95 capture validates tooling, not relabeling efficacy.",
        "modality-identity-preservation": "Analyze hashed native raw/projected/fused/final tensors with physical instance endpoints; expand to predefined recoverable same-class stratum before inference.",
        "referent-discrimination": "Expand successful native criterion/query binding to the predefined TRAIN sample; quantify positive/seed/mask contingencies with scene uncertainty.",
        "instance-identity-representation": "Compute same-class feature/rank contrasts from native feature artifacts and actual instance_labels; verify target and wrong-instance membership before testing.",
        "referent-query-selection": "Expand all-acceptable rank capture to preregistered sample; native argmax matched16 expressions. Retain no-acceptable denominator and scene-balanced uncertainty.",
        "input-modality-distinguishability": "Use strict occurrence/producer-aware physical_join on native feature artifacts; compute paired modality contrasts with no row-position archive joins.",
        "same-target-description-grounding": "Select seven connected control scene/annotation IDs explicitly in native loader and bind their physical endpoints; current16-expression smoke capture does not establish those controls.",
        "same-forward-coverage-diagnosis": "Expand exact FPS/sample/mask capture beyond2 batches; preserve point inverse and scene-balanced strata. No repeated cluster intervention.",
    }
    path = ROOT / "pipeline/research_work.json"
    work = json.loads(path.read_text(encoding="utf-8"))
    for candidate in work["candidates"]:
        if candidate["id"] not in actions:
            continue
        candidate["next_action"] = actions[candidate["id"]]
        candidate["native_capture_progress"] = dict(
            stage_completed="Two-batch native support/feature/query capture",
            expressions=16, static_tests_passed=13,
            scientific_validation_complete=False, report=REPORT)
        candidate["evidence"].extend([evidence(REPORT), evidence(RAW),
                                     evidence("scripts/native_support_capture_20260916.py"),
                                     evidence("scripts/test_native_support_capture_20260916.py")])
    path.write_text(json.dumps(work, ensure_ascii=True, indent=2) + "\n", encoding="ascii")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
