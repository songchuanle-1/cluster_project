"""Persist the exact-capture reproducibility gate into research_work.json."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORK_PATH = ROOT / "pipeline" / "research_work.json"
RECEIPT_PATH = (
    ROOT
    / "pipeline"
    / "reports"
    / "m95_exact_capture_reproducibility_gate_20260925-0132.json"
)
RECEIPT_SHA256 = (
    "5fe0b1f49285a8234bd4ab300183e992433854eb21685b75ae3ae51bef6b1703"
)
DECISION_PATH = (
    ROOT / "pipeline" / "decisions" / "20260925-013205_route_change.md"
)
DECISION_SHA256 = (
    "3786b044f2f34b74fb646d58a2cec80d0854add594dffe45b48800ad72244332"
)
DUE_IDS = (
    "referent-supervision-axis",
    "referent-discrimination",
    "instance-identity-representation",
)
TIMESTAMP = "2026-09-25T01:32:05+08:00"
NEXT_ACTION = (
    "Monitor exact capture PID 3140840 to completion. Then run the updated "
    "scripts/m95_exact_capture_postprocess_20260925.py with fresh component, "
    "identity-control, identity-analysis, reproducibility and receipt outputs. "
    "The runner must pass completion, provenance, manifest, checkpoint, artifact "
    "coverage and 256-row reproducibility gates before any analyzer result is "
    "treated as causal evidence. No admission, native backward or resource claim "
    "is available yet."
)


def add_evidence(candidate, path, sha256):
    evidence = candidate.setdefault("evidence", [])
    entry = {"path": path, "sha256": sha256}
    for index, current in enumerate(evidence):
        if current.get("path") == path:
            evidence[index] = entry
            return
    evidence.append(entry)


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if file_sha256(RECEIPT_PATH) != RECEIPT_SHA256:
        raise ValueError("Reproducibility receipt hash differs")
    if file_sha256(DECISION_PATH) != DECISION_SHA256:
        raise ValueError("Decision record hash differs")

    document = json.loads(WORK_PATH.read_text(encoding="utf-8"))
    found = set()
    progress = {
        "timestamp": TIMESTAMP,
        "stage": "validation",
        "implementation_complete": True,
        "native_execution_completed": False,
        "exact_capture_ready": False,
        "reproducibility_gate_required": True,
        "comparison_rows": 256,
        "numeric_tolerance": 1e-6,
        "focused_tests_passed": 17,
        "dependent_tests_passed": 38,
        "remote_focused_tests_passed": 17,
        "receipt": {
            "path": RECEIPT_PATH.relative_to(ROOT).as_posix(),
            "sha256": RECEIPT_SHA256,
        },
        "decision": {
            "path": DECISION_PATH.relative_to(ROOT).as_posix(),
            "sha256": DECISION_SHA256,
        },
        "admission": False,
    }
    for candidate in document["candidates"]:
        if candidate.get("id") not in DUE_IDS:
            continue
        found.add(candidate["id"])
        candidate["stage"] = "validation"
        candidate["next_action"] = NEXT_ACTION
        candidate["reproducibility_gate_20260925"] = progress
        add_evidence(
            candidate,
            RECEIPT_PATH.relative_to(ROOT).as_posix(),
            RECEIPT_SHA256,
        )
        add_evidence(
            candidate,
            DECISION_PATH.relative_to(ROOT).as_posix(),
            DECISION_SHA256,
        )
    if found != set(DUE_IDS):
        raise ValueError("Due candidate set differs")

    document["updated_at"] = TIMESTAMP
    document["next_action"] = NEXT_ACTION
    document["design_cycle"] = {
        "timestamp": TIMESTAMP,
        "stop_reason": "exact_full_scan_running_after_reproducibility_gate",
        "attempted_ids": list(DUE_IDS),
        "evidence": [
            {
                "path": RECEIPT_PATH.relative_to(ROOT).as_posix(),
                "sha256": RECEIPT_SHA256,
            },
            {
                "path": DECISION_PATH.relative_to(ROOT).as_posix(),
                "sha256": DECISION_SHA256,
            },
        ],
        "resume_condition": (
            "Resume PID 3140840 at capture completion, run the updated "
            "fail-closed postprocess runner, require the 256-row identity "
            "analysis to reproduce selector choices and numeric behavior, then "
            "evaluate component and identity-query outputs before mechanism "
            "derivation or admission."
        ),
    }
    temporary = WORK_PATH.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(
            document,
            indent=2,
            ensure_ascii=False,
            sort_keys=False,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(WORK_PATH)
    print(
        json.dumps(
            {
                "updated_at": document["updated_at"],
                "candidate_ids": sorted(found),
                "stop_reason": document["design_cycle"]["stop_reason"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
