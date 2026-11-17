"""Persist the native semantic recovery result without admitting a mechanism."""

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK_PATH = ROOT / "pipeline" / "research_work.json"
QUEUE_PATH = ROOT / "pipeline" / "queue.json"
REPORT = (
    ROOT
    / "pipeline"
    / "reports"
    / "m95_semantic_identity_recovery_20260922-1048.json"
)
SCRIPT = ROOT / "scripts" / "m95_semantic_identity_recovery_20260922.py"
TEST = ROOT / "scripts" / "test_m95_semantic_identity_recovery_20260922.py"
CAPTURE = (
    ROOT
    / "pipeline"
    / "diagnostic_runs"
    / "m95_same_forward_20260922-0945"
    / "capture.json"
)
DECISION = (
    ROOT
    / "pipeline"
    / "decisions"
    / "20260922-105514_route_change.md"
)
EXPECTED_REPORT_SHA256 = (
    "8e544613a5d6413efd1a44a6ffea36de04b47f5335660b99aed19c3227c93ae0"
)
EXPECTED_SCRIPT_SHA256 = (
    "8d0149b0d98315b5bd464788a4998778b4d84e83f02217803fca193b3c6618f6"
)
EXPECTED_TEST_SHA256 = (
    "43984150852c93eb9cec9a44e69acd97aa38d7fd5e845b2f5d9910b2723662b3"
)
EXPECTED_CAPTURE_SHA256 = (
    "975c718ddefb122ef8368c117439e9562b9893bb40abf8d80d1fc31c05824c80"
)

AXIS_ID = "referent-supervision-axis"
DIAGNOSIS_IDS = (
    "referent-causality-audit",
    "referent-discrimination",
    "instance-identity-representation",
    "modality-identity-preservation",
)

NEXT_ACTIONS = {
    "referent-causality-audit": (
        "Pre-register a larger same-forward manifest with a class-matched "
        "objectness control and an identity control; require complete "
        "target/wrong/acceptable-query semantics and no fallback. Do not admit "
        "or enqueue a mechanism from the bounded 16-row capture."
    ),
    "referent-discrimination": (
        "Pre-register a larger same-class discrimination cohort containing "
        "target, wrong same-class, acceptable same-class, and cross-class "
        "controls. Keep the route diagnostic until the population-level "
        "separation and rejection criteria are fixed and observed."
    ),
    "instance-identity-representation": (
        "Pre-register a larger per-stage identity-separability test with "
        "adequate per-instance support, complete semantics, and class-matched "
        "controls. Retain the final-stage identity hypothesis only as "
        "falsifiable diagnostic work."
    ),
    "modality-identity-preservation": (
        "Pre-register per-modality identity-relation preservation on a larger "
        "same-forward manifest with class-matched controls and predeclared "
        "degradation criteria. Do not derive a fusion or projection variant "
        "from the bounded capture."
    ),
}


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path):
    return str(Path(path).relative_to(ROOT)).replace("\\", "/")


def add_evidence(candidate, records):
    existing = {
        (item["path"], item["sha256"])
        for item in candidate.setdefault("evidence", [])
    }
    for record in records:
        key = (record["path"], record["sha256"])
        if key not in existing:
            candidate["evidence"].append(record)
            existing.add(key)


def verify_inputs():
    expected = {
        REPORT: EXPECTED_REPORT_SHA256,
        SCRIPT: EXPECTED_SCRIPT_SHA256,
        TEST: EXPECTED_TEST_SHA256,
        CAPTURE: EXPECTED_CAPTURE_SHA256,
    }
    for path, digest in expected.items():
        if file_sha256(path) != digest:
            raise ValueError("Evidence hash mismatch: %s" % path)
    if not DECISION.is_file():
        raise ValueError("Decision record is missing")

    report = json.loads(REPORT.read_text(encoding="utf-8"))
    summary = report["summary"]
    if summary != {
        "selected_query_failures": 8,
        "previously_semantic_unresolved": 6,
        "recovered": 6,
        "same_class_phrase": 6,
        "cross_class_name": 0,
        "combined_known_same_class_failures": 8,
        "combined_known_cross_class_failures": 0,
    }:
        raise ValueError("Unexpected semantic recovery summary")
    return report


def main():
    report = verify_inputs()
    work_hash = file_sha256(WORK_PATH)
    queue_hash = file_sha256(QUEUE_PATH)
    evidence = [
        {"path": relative(REPORT), "sha256": EXPECTED_REPORT_SHA256},
        {"path": relative(SCRIPT), "sha256": EXPECTED_SCRIPT_SHA256},
        {"path": relative(TEST), "sha256": EXPECTED_TEST_SHA256},
        {"path": relative(CAPTURE), "sha256": EXPECTED_CAPTURE_SHA256},
        {"path": relative(DECISION), "sha256": file_sha256(DECISION)},
    ]
    progress = {
        "timestamp": "2026-09-22T10:48:00+08:00",
        "report": relative(REPORT),
        "report_sha256": EXPECTED_REPORT_SHA256,
        "script": relative(SCRIPT),
        "script_sha256": EXPECTED_SCRIPT_SHA256,
        "tests_passed": 4,
        "selected_query_failures": 8,
        "previously_semantic_unresolved": 6,
        "recovered_same_class": 6,
        "combined_known_same_class_failures": 8,
        "combined_known_cross_class_failures": 0,
        "scene_graph_index": "ann_id",
        "objectness_control_class_matched": False,
        "referent_causality_resolved": False,
        "admission": False,
        "native_sources": report["native_sources"],
    }

    work = json.loads(WORK_PATH.read_text(encoding="utf-8"))
    candidates = {candidate["id"]: candidate for candidate in work["candidates"]}
    target_ids = (AXIS_ID, *DIAGNOSIS_IDS)
    missing = [identifier for identifier in target_ids if identifier not in candidates]
    if missing:
        raise ValueError("Missing candidates: %s" % ", ".join(missing))

    axis = candidates[AXIS_ID]
    axis["stage"] = "design"
    axis["latest_progress"] = (
        "2026-09-22T10:48:00+08:00: native semantic recovery classified all "
        "six previously unresolved M95 failure pairs as same-class; all 8/8 "
        "selected-query failures are now known same-class identity confusions. "
        "The objectness-only any-seed control is not class-matched, so this "
        "does not isolate referent-specific causality or admit a mechanism."
    )
    axis["next_action"] = (
        "Keep the supervision axis design-only. Pre-register the larger "
        "same-forward manifest with complete semantics and class-matched "
        "objectness/identity controls before any admission chain. Do not fill "
        "capacity with a renamed or confounded mechanism."
    )
    axis["semantic_identity_recovery_20260922_1048"] = progress
    add_evidence(axis, evidence)

    for identifier in DIAGNOSIS_IDS:
        candidate = candidates[identifier]
        candidate["stage"] = "diagnosis"
        candidate["latest_progress"] = (
            "2026-09-22T10:48:00+08:00: recovered native semantics for six "
            "M95 selected-query failures using ScanRefer object_id -> ann_id "
            "and annotation-indexed scene graphs. All six recovered pairs are "
            "same-class; combined with the two prior known pairs, 8/8 failures "
            "are same-class and 0/8 are cross-class-name. The any-seed "
            "objectness control is not class-matched, so referent identity "
            "remains confounded with same-class objectness. Bounded diagnostic "
            "only; admission remains false."
        )
        candidate["next_action"] = NEXT_ACTIONS[identifier]
        candidate["semantic_identity_recovery_20260922_1048"] = progress
        add_evidence(candidate, evidence)

    work["next_action"] = (
        "Pre-register a larger same-forward manifest with complete native "
        "target/wrong/acceptable-query semantics and class-matched objectness "
        "and identity controls. Keep all four diagnosis routes and the "
        "supervision axis admission=false; do not mutate the queue or launch."
    )
    work["updated_at"] = "2026-09-22T10:55:14+08:00"

    if file_sha256(WORK_PATH) != work_hash:
        raise ValueError("Concurrent research_work mutation")
    if file_sha256(QUEUE_PATH) != queue_hash:
        raise ValueError("Concurrent queue mutation")

    temporary = WORK_PATH.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(work, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    os.replace(temporary, WORK_PATH)

    if file_sha256(QUEUE_PATH) != queue_hash:
        raise ValueError("Queue changed during persistence")
    result = json.loads(WORK_PATH.read_text(encoding="utf-8"))
    updated = {candidate["id"] for candidate in result["candidates"]}
    if not set(target_ids).issubset(updated):
        raise ValueError("Persistence lost a target candidate")
    print(
        json.dumps(
            {
                "updated_ids": list(target_ids),
                "report_sha256": EXPECTED_REPORT_SHA256,
                "decision_sha256": file_sha256(DECISION),
                "queue_sha256": queue_hash,
                "admission": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
