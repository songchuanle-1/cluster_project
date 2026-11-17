"""Derive bounded controls from the frozen M95 same-forward capture.

This is a CPU-only analysis of an existing capture. It changes only the query
selection rule; it does not rerun the model or claim deployable efficacy.
"""
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CAPTURE = (
    ROOT
    / "pipeline"
    / "diagnostic_runs"
    / "m95_same_forward_20260922-0945"
    / "capture.json"
)
OUTPUT = ROOT / "pipeline" / "reports" / "m95_same_forward_control_20260922-0955.json"
REMOTE_CAPTURE = (
    "/data3/songcl/Project/Cluster_project/pipeline/diagnostic_runs/"
    "m95_same_forward_20260922-0945/capture.json"
)
EXPECTED_CAPTURE_SHA256 = (
    "975c718ddefb122ef8368c117439e9562b9893bb40abf8d80d1fc31c05824c80"
)
EXPECTED_CHECKPOINT_SHA256 = (
    "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
)
SELECTION_KEYS = (
    "deployed_success",
    "positive_success",
    "anyseed_success",
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pick(scores, allowed):
    if len(scores) != len(allowed):
        raise ValueError("Query score and control length differ")
    indices = [index for index, value in enumerate(allowed) if bool(value)]
    if not indices:
        best = max(range(len(scores)), key=lambda index: (scores[index], -index))
        return best, False
    return max(indices, key=lambda index: (scores[index], -index)), True


def bootstrap(values, draws=10000, seed=1999):
    if not values:
        raise ValueError("Cannot bootstrap an empty sample")
    rng = random.Random(seed)
    means = [
        sum(rng.choices(values, k=len(values))) / len(values)
        for _ in range(draws)
    ]
    means.sort()
    return {
        "mean": sum(means) / len(means),
        "lo": means[int(0.025 * (draws - 1))],
        "hi": means[int(0.975 * (draws - 1))],
    }


def main():
    if file_sha256(CAPTURE) != EXPECTED_CAPTURE_SHA256:
        raise ValueError("Capture hash differs from the frozen receipt")
    document = json.loads(CAPTURE.read_text(encoding="utf-8"))
    if document.get("checkpoint_sha256") != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError("Capture checkpoint identity differs")
    if document.get("native_capture_completed") is not True:
        raise ValueError("Capture is not complete")
    rows = document.get("rows")
    if not isinstance(rows, list) or len(rows) != 16:
        raise ValueError("Expected the bounded 16-expression capture")

    observed = []
    for row in rows:
        scores = row["scores"]
        ious = row["ious"]
        if len(scores) != len(ious) or not scores:
            raise ValueError("Invalid query axes")
        if any(not math.isfinite(value) for value in scores + ious):
            raise ValueError("Nonfinite query evidence")
        if row["selected_query"] != max(
                range(len(scores)), key=lambda index: (scores[index], -index)):
            raise ValueError("Selected query differs from native argmax")
        deployed, _ = pick(scores, [True] * len(scores))
        positive, positive_available = pick(scores, row["native_positive"])
        anyseed, anyseed_available = pick(scores, row["seed_inside"])
        observed.append({
            "scene": row["scene"],
            "ann_id": int(row["ann_id"]),
            "expression_slot": int(row["expression_slot"]),
            "selected_query": int(row["selected_query"]),
            "deployed_query": int(deployed),
            "positive_query": int(positive),
            "anyseed_query": int(anyseed),
            "deployed_success": bool(ious[deployed] > 0.5),
            "positive_success": bool(ious[positive] > 0.5),
            "anyseed_success": bool(ious[anyseed] > 0.5),
            "positive_available": bool(positive_available),
            "anyseed_available": bool(anyseed_available),
            "n_positive": int(sum(bool(value) for value in row["native_positive"])),
            "n_anyseed": int(sum(bool(value) for value in row["seed_inside"])),
            "deployed_iou": float(ious[deployed]),
            "positive_iou": float(ious[positive]),
            "anyseed_iou": float(ious[anyseed]),
            "best_acceptable_rank": (
                None if row["best_acceptable_rank"] is None
                else int(row["best_acceptable_rank"])
            ),
            "recoverable_same_class": bool(row["recoverable_same_class"]),
        })

    by_scene = defaultdict(list)
    for row in observed:
        by_scene[row["scene"]].append(row)

    summaries = {}
    for key in SELECTION_KEYS:
        scene_rates = [
            sum(bool(row[key]) for row in group) / len(group)
            for group in by_scene.values()
        ]
        summaries[key] = {
            "pooled": sum(bool(row[key]) for row in observed) / len(observed),
            "scene_balanced": sum(scene_rates) / len(scene_rates),
            "scene_bootstrap_95ci": bootstrap(scene_rates),
        }

    deltas = [
        int(row["positive_success"]) - int(row["deployed_success"])
        for row in observed
    ]
    scene_deltas = [
        sum(int(row["positive_success"]) - int(row["deployed_success"])
            for row in group) / len(group)
        for group in by_scene.values()
    ]
    observed_failures = [row for row in observed if not row["deployed_success"]]
    acceptable_ranks = [
        row["best_acceptable_rank"] for row in observed
        if row["best_acceptable_rank"] is not None
    ]
    rank_summary = {
        "selected_success": sum(row["deployed_success"] for row in observed),
        "selected_failures": len(observed_failures),
        "no_acceptable": sum(
            row["best_acceptable_rank"] is None for row in observed
        ),
        "best_acceptable_rank_min": min(acceptable_ranks),
        "best_acceptable_rank_max": max(acceptable_ranks),
        "failure_rank_values": [
            row["best_acceptable_rank"] for row in observed_failures
        ],
        "failure_recoverable_same_class": sum(
            bool(row["recoverable_same_class"]) for row in observed_failures
        ),
    }
    result = {
        "contract": "m95_same_forward_control_derivation_v1",
        "generated_at": "2026-09-22T09:55:00+08:00",
        "scope": (
            "CPU-only derived control from one completed 2-batch native M95 "
            "same-forward capture. Only the query selection rule changes; "
            "checkpoint, query set and scores are untouched."
        ),
        "source_capture": {
            "local_path": CAPTURE.relative_to(ROOT).as_posix(),
            "local_sha256": file_sha256(CAPTURE),
            "remote_path": REMOTE_CAPTURE,
            "remote_sha256": EXPECTED_CAPTURE_SHA256,
        },
        "binding": {
            "checkpoint_sha256": document["checkpoint_sha256"],
            "model_source_sha256": document["model_source_sha256"],
            "config_sha256": document["config_sha256"],
            "producer_sha256": document["producer_sha256"],
            "native_capture_completed": document["native_capture_completed"],
        },
        "summary": {
            "expressions": len(observed),
            "scenes": len(by_scene),
            "positive_available": (
                sum(row["positive_available"] for row in observed) / len(observed)
            ),
            "anyseed_available": (
                sum(row["anyseed_available"] for row in observed) / len(observed)
            ),
            "mean_positives_per_expression": (
                sum(row["n_positive"] for row in observed) / len(observed)
            ),
            "mean_anyseed_per_expression": (
                sum(row["n_anyseed"] for row in observed) / len(observed)
            ),
            "success": summaries,
            "paired_delta_positive_minus_deployed": {
                "pooled": sum(deltas) / len(deltas),
                "scene_balanced": sum(scene_deltas) / len(scene_deltas),
                "scene_bootstrap_95ci": bootstrap(scene_deltas),
            },
            "fixed": sum(
                row["positive_success"] and not row["deployed_success"]
                for row in observed
            ),
            "broken": sum(
                row["deployed_success"] and not row["positive_success"]
                for row in observed
            ),
            "referent_discrimination": rank_summary,
        },
        "rows": observed,
        "interpretation": (
            "This is a bounded diagnostic on 16 TRAIN expressions. Positive "
            "selection uses training labels and is an oracle upper bound, not "
            "a deployable result. Any-seed selection is the objectness-only "
            "control. It does not establish population effect, admission, "
            "efficacy, novelty or target-independent objectness."
        ),
        "not_evidence_of": [
            "admission",
            "efficacy",
            "independence",
            "novelty",
            "population effect",
            "target-independent objectness",
            "referent-specific causality when the any-seed control also improves",
        ],
    }
    OUTPUT.write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
