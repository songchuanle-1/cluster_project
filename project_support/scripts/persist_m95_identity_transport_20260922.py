"""Persist the server-6 transport interruption for the five identity candidates."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "pipeline" / "research_work.json"
RECEIPT = "pipeline/reports/m95_identity_validation_transport_20260922-2030.json"
DECISION = "pipeline/decisions/20260922-203332_route_change.md"
DUE = {
    "referent-supervision-axis",
    "referent-causality-audit",
    "modality-identity-preservation",
    "referent-discrimination",
    "instance-identity-representation",
}
BLOCKER = (
    "Server-6 is unreachable from the orchestration host: the 20:16 monitor "
    "preflight reported it unreachable and a direct BatchMode SSH probe "
    "received no response before local termination."
)
RETRY_AFTER = "2026-09-22T21:30:00+08:00"
UNBLOCK = (
    "SSH to server-6 succeeds; GPU7 occupancy is verified without disturbing "
    "foreign work; the unique producer log shows increasing native steps or a "
    "completed capture; capture.json exists and all 256 frozen manifest rows "
    "match before the hash-bound analyzer is run."
)
NEXT_ACTION = (
    "Retry the server-6 transport check at or after 2026-09-22T21:30:00+08:00. "
    "If reachable, verify the existing capture log and GPU safety before any "
    "replacement launch. If complete, run the hash-bound analyzer and resolve "
    "the pre-registered gates. Do not start a replacement capture or new design "
    "while the shared validation transport is blocked."
)


def sha256(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    receipt_hash = sha256(RECEIPT)
    decision_hash = sha256(DECISION)
    work = json.loads(WORK.read_text(encoding="utf-8"))
    touched = []
    for candidate in work["candidates"]:
        if candidate.get("id") not in DUE:
            continue
        candidate["stage"] = "blocked"
        candidate["blocker"] = BLOCKER
        candidate["retry_after"] = RETRY_AFTER
        candidate["unblock_condition"] = UNBLOCK
        candidate["next_action"] = NEXT_ACTION
        candidate["transport_progress"] = {
            "report": RECEIPT,
            "report_sha256": receipt_hash,
            "decision": DECISION,
            "decision_sha256": decision_hash,
            "state": "transport_unavailable",
            "retry_after": RETRY_AFTER,
        }
        existing = {entry["path"] for entry in candidate.get("evidence", [])}
        for path, digest in (
            (RECEIPT, receipt_hash),
            (DECISION, decision_hash),
        ):
            if path not in existing:
                candidate.setdefault("evidence", []).append(
                    {"path": path, "sha256": digest}
                )
        touched.append(candidate["id"])

    if set(touched) != DUE:
        raise ValueError("Due candidate set mismatch: %s" % sorted(touched))

    work["updated_at"] = "2026-09-22T20:34:00+08:00"
    work["next_action"] = NEXT_ACTION
    work["last_event_tick"] = {
        "timestamp": "2026-09-22T20:34:00+08:00",
        "mode": "event",
        "due_ids": sorted(DUE),
        "result": (
            "The server-6 transport was unavailable at the monitor preflight "
            "and remained unavailable during a direct SSH probe. The five "
            "shared identity-validation candidates were marked temporarily "
            "blocked at the transport boundary. No queue entry, capture, "
            "admission, rejection, scientific result, or GPU execution was "
            "created."
        ),
        "next_action": NEXT_ACTION,
        "evidence": [
            {"path": RECEIPT, "sha256": receipt_hash},
            {"path": DECISION, "sha256": decision_hash},
        ],
    }
    with WORK.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(work, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print("updated %d candidates" % len(touched))


if __name__ == "__main__":
    main()
