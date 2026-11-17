"""Persist the latest progress of the frozen M95 identity-capture validation."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "pipeline" / "research_work.json"
RECEIPT = "pipeline/reports/m95_identity_capture_progress_20260922-2324.json"
DUE = {
    "referent-supervision-axis",
    "referent-causality-audit",
    "modality-identity-preservation",
    "referent-discrimination",
    "instance-identity-representation",
}
NEXT_ACTION = (
    "Continue monitoring existing server-6 PID 1578754 and its log until "
    "capture.json exists. Then verify all 256 frozen manifest rows remain "
    "hash-bound before running "
    "analyze_m95_manifest_identity_controls_20260922.py. Do not start a "
    "replacement capture, admission, rejection, queue mutation, or new design "
    "while this shared validation is incomplete."
)
UNBLOCK_CONDITION = (
    "The existing producer completes with capture.json present and all 256 "
    "frozen manifest rows match the pre-registered manifest and producer "
    "hashes before the hash-bound analyzer is run."
)


def sha256(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    receipt_hash = sha256(RECEIPT)
    work = json.loads(WORK.read_text(encoding="utf-8"))
    touched = []
    for candidate in work["candidates"]:
        if candidate.get("id") not in DUE:
            continue
        candidate["stage"] = "validation"
        candidate["blocker"] = None
        candidate["retry_after"] = None
        candidate["unblock_condition"] = UNBLOCK_CONDITION
        candidate["next_action"] = NEXT_ACTION
        progress = candidate.setdefault("identity_capture_progress", {})
        progress.update(
            {
                "report": RECEIPT,
                "report_sha256": receipt_hash,
                "state": "pending_progress",
                "pid": 1578754,
                "started_at": "2026-09-22T18:13:00+08:00",
                "last_step": 4533,
                "last_expressions": 246,
                "expected_expressions": 256,
                "capture_json_present": False,
                "output_dir": (
                    "/data3/songcl/Project/Cluster_project/pipeline/"
                    "diagnostic_runs/m95_identity_capture_20260922-1813"
                ),
                "log_path": (
                    "/data3/songcl/Project/Cluster_project/pipeline/logs/"
                    "m95_identity_capture_20260922-1813.log"
                ),
            }
        )
        if "transport_progress" in candidate:
            candidate["transport_progress"]["state"] = "reachable"
            candidate["transport_progress"]["latest_progress_report"] = RECEIPT
        existing = {entry["path"] for entry in candidate.get("evidence", [])}
        if RECEIPT not in existing:
            candidate.setdefault("evidence", []).append(
                {"path": RECEIPT, "sha256": receipt_hash}
            )
        touched.append(candidate["id"])

    if set(touched) != DUE:
        raise ValueError("Due candidate set mismatch: %s" % sorted(touched))

    work["updated_at"] = "2026-09-22T23:24:11+08:00"
    work["next_action"] = NEXT_ACTION
    work["last_event_tick"] = {
        "timestamp": "2026-09-22T23:24:11+08:00",
        "mode": "event",
        "due_ids": sorted(DUE),
        "result": (
            "The existing server-6 PID 1578754 remains alive and the same "
            "capture advanced from step 3747 / 206 expressions to step 4533 / "
            "246 of 256 expressions. capture.json remains absent, so the five "
            "shared identity-validation candidates remain in validation. No "
            "analysis, admission, rejection, queue mutation, replacement "
            "capture, or GPU launch was created."
        ),
        "next_action": NEXT_ACTION,
        "evidence": [{"path": RECEIPT, "sha256": receipt_hash}],
    }
    with WORK.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(work, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print("updated %d candidates" % len(touched))


if __name__ == "__main__":
    main()
