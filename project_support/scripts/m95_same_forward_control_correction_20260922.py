"""Correct the unavailable any-seed fallback in the M95 control receipt.

The source capture and original control receipt remain immutable. This script
recomputes the control summary with one explicit rule: if no query contains a
seed inside any instance, the any-seed rule has no valid candidate and counts as
unsuccessful rather than falling back to the deployed argmax.
"""
import hashlib
import json
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
CONTROL = (
    ROOT
    / "pipeline"
    / "reports"
    / "m95_same_forward_control_20260922-0955.json"
)
OUTPUT = (
    ROOT
    / "pipeline"
    / "reports"
    / "m95_same_forward_control_correction_20260922-1030.json"
)
EXPECTED_CAPTURE_SHA256 = (
    "975c718ddefb122ef8368c117439e9562b9893bb40abf8d80d1fc31c05824c80"
)
EXPECTED_CONTROL_SHA256 = (
    "8f6cd55f2edf61dd4af05780108838444871af6194876ba35fcc4b777564d2ab"
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def corrected_anyseed(row):
    """Return (success, iou, query, fallback_was_used)."""
    if bool(row["anyseed_available"]):
        return (
            bool(row["anyseed_success"]),
            float(row["anyseed_iou"]),
            int(row["anyseed_query"]),
            False,
        )
    return False, None, None, True


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


def summarize(rows, key):
    by_scene = defaultdict(list)
    for row in rows:
        by_scene[row["scene"]].append(bool(row[key]))
    scene_rates = [
        sum(group) / len(group)
        for group in by_scene.values()
    ]
    return {
        "pooled": sum(bool(row[key]) for row in rows) / len(rows),
        "scene_balanced": sum(scene_rates) / len(scene_rates),
        "scene_bootstrap_95ci": bootstrap(scene_rates),
    }


def paired_delta(rows, candidate_key, baseline_key="deployed_success"):
    by_scene = defaultdict(list)
    for row in rows:
        by_scene[row["scene"]].append(
            int(bool(row[candidate_key])) - int(bool(row[baseline_key]))
        )
    scene_deltas = [
        sum(group) / len(group)
        for group in by_scene.values()
    ]
    return {
        "pooled": sum(
            int(bool(row[candidate_key])) - int(bool(row[baseline_key]))
            for row in rows
        )
        / len(rows),
        "scene_balanced": sum(scene_deltas) / len(scene_deltas),
        "scene_bootstrap_95ci": bootstrap(scene_deltas),
    }


def build_correction(capture, control):
    if capture.get("native_capture_completed") is not True:
        raise ValueError("Capture is not complete")
    if control.get("source_capture", {}).get("local_sha256") != EXPECTED_CAPTURE_SHA256:
        raise ValueError("Control receipt does not bind the frozen capture")
    rows = []
    fallback_count = 0
    for source in control["rows"]:
        success, iou, query, fallback = corrected_anyseed(source)
        fallback_count += int(fallback)
        rows.append({
            "scene": source["scene"],
            "ann_id": int(source["ann_id"]),
            "expression_slot": int(source["expression_slot"]),
            "deployed_success": bool(source["deployed_success"]),
            "positive_success": bool(source["positive_success"]),
            "anyseed_available": bool(source["anyseed_available"]),
            "anyseed_success_original": bool(source["anyseed_success"]),
            "anyseed_success_corrected": bool(success),
            "anyseed_iou_corrected": iou,
            "anyseed_query_corrected": query,
            "fallback_correction_applied": bool(fallback),
        })
    return {
        "contract": "m95_same_forward_control_correction_v1",
        "generated_at": "2026-09-22T10:30:00+08:00",
        "scope": (
            "CPU-only correction of one fallback in the any-seed objectness "
            "control. No model forward, queue mutation, admission, or training."
        ),
        "source_capture": {
            "path": CAPTURE.relative_to(ROOT).as_posix(),
            "sha256": EXPECTED_CAPTURE_SHA256,
        },
        "source_control": {
            "path": CONTROL.relative_to(ROOT).as_posix(),
            "sha256": EXPECTED_CONTROL_SHA256,
        },
        "correction_rule": (
            "When no query contains a seed inside any instance, the any-seed "
            "control has no valid candidate and is counted unsuccessful. The "
            "deployed argmax is not substituted."
        ),
        "fallback_rows_corrected": fallback_count,
        "summary": {
            "expressions": len(rows),
            "deployed_success": summarize(rows, "deployed_success"),
            "positive_success": summarize(rows, "positive_success"),
            "anyseed_success_original": summarize(rows, "anyseed_success_original"),
            "anyseed_success_corrected": summarize(rows, "anyseed_success_corrected"),
        },
        "paired_delta": {
            "positive_minus_deployed": paired_delta(rows, "positive_success"),
            "anyseed_corrected_minus_deployed": paired_delta(
                rows, "anyseed_success_corrected"
            ),
        },
        "counts": {
            "deployed_success": sum(row["deployed_success"] for row in rows),
            "positive_success": sum(row["positive_success"] for row in rows),
            "anyseed_success_original": sum(
                row["anyseed_success_original"] for row in rows
            ),
            "anyseed_success_corrected": sum(
                row["anyseed_success_corrected"] for row in rows
            ),
            "anyseed_available": sum(row["anyseed_available"] for row in rows),
    },
        "rows": rows,
        "interpretation": (
            "The original control receipt already records 15/16 positive and "
            "any-seed success; the 09:50 narrative claim of 13/16 is a downstream "
            "misquote. After correcting the unavailable any-seed fallback, the "
            "any-seed control still improves over deployed selection. The "
            "referent-identity claim remains confounded and is not admission "
            "evidence."
        ),
        "not_evidence_of": [
            "admission",
            "efficacy",
            "population effect",
            "referent-specific causality",
            "target-independent objectness",
        ],
    }


def main():
    capture_hash = file_sha256(CAPTURE)
    control_hash = file_sha256(CONTROL)
    if capture_hash != EXPECTED_CAPTURE_SHA256:
        raise ValueError("Capture hash changed")
    if control_hash != EXPECTED_CONTROL_SHA256:
        raise ValueError("Control hash changed")
    capture = json.loads(CAPTURE.read_text(encoding="utf-8"))
    control = json.loads(CONTROL.read_text(encoding="utf-8"))
    result = build_correction(capture, control)
    OUTPUT.write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps(result["counts"], sort_keys=True))
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
