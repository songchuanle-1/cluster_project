"""Persist the 09:20 event retry without changing candidate scope."""

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_WORK = ROOT / "pipeline" / "research_work.json"
REPORT = ROOT / "pipeline" / "reports" / "event_due_resume_20260922-0920.json"
DECISION = (
    ROOT
    / "pipeline"
    / "decisions"
    / "20260922-092104_route_change.md"
)

OPEN_ID = "referent-supervision-axis"
BLOCKED_IDS = (
    "referent-causality-audit",
    "referent-discrimination",
    "instance-identity-representation",
    "modality-identity-preservation",
)


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path):
    return str(path.relative_to(ROOT)).replace("\\", "/")


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


def main():
    report_record = {
        "path": relative(REPORT),
        "sha256": file_sha256(REPORT),
    }
    decision_record = {
        "path": relative(DECISION),
        "sha256": file_sha256(DECISION),
    }
    evidence = [report_record, decision_record]

    work = json.loads(RESEARCH_WORK.read_text(encoding="utf-8"))
    candidates = {candidate["id"]: candidate for candidate in work["candidates"]}
    timestamp = "2026-09-22T09:20:41+08:00"

    open_axis = candidates[OPEN_ID]
    open_axis["stage"] = "design"
    open_axis["latest_progress"] = (
        timestamp
        + ": event retry confirmed server-6 reachability and allowed GPU7 "
        "capacity, but did not authorize or create a new design candidate."
    )
    add_evidence(open_axis, evidence)

    for identifier in BLOCKED_IDS:
        candidate = candidates[identifier]
        candidate["stage"] = "blocked"
        candidate["latest_progress"] = (
            timestamp
            + ": event retry reached server-6 and observed GPU7 with 39536 MiB "
            "free. The exact M95 checkpoint directory remained absent under "
            "allowed storage, so the frozen native capture could not run."
        )
        candidate["blocker"] = (
            "The exact M95 checkpoint payload is absent from allowed server-6 "
            "storage; server reachability and GPU7 capacity are no longer blockers."
        )
        candidate["retry_after"] = "2026-09-22T10:20:00+08:00"
        candidate["unblock_condition"] = (
            "An exact M95 checkpoint payload is present under allowed server-6 "
            "storage with a frozen hash; then run the deployed frozen capture on "
            "GPU7 without evicting foreign work."
        )
        candidate["alternatives_attempted"] = (
            "The scheduled 09:20 SSH retry succeeded, GPU7 capacity was measured "
            "without touching foreign work, and the exact allowed checkpoint "
            "directory was tested. No unauthorized host, checkpoint "
            "substitution, or local training fallback was used."
        )
        candidate["next_action"] = (
            "At the next scheduled retry, verify the exact M95 checkpoint payload "
            "under allowed storage. If absent, remain blocked; if present, run "
            "the frozen native capture before proposing a successor."
        )
        candidate["due_resolution_20260922_0920"] = {
            "disposition": "external_blocker",
            "reason": (
                "The frozen identity contract requires the exact M95 checkpoint; "
                "the allowed directory is missing, so capture cannot run."
            ),
            "evidence": evidence,
            "blocker": candidate["blocker"],
            "retry_after": candidate["retry_after"],
            "unblock_condition": candidate["unblock_condition"],
            "alternatives_attempted": candidate["alternatives_attempted"],
        }
        add_evidence(candidate, evidence)

    work["last_event_tick"] = {
        "timestamp": timestamp,
        "mode": "event",
        "due_ids": [OPEN_ID, *BLOCKED_IDS],
        "evidence": evidence,
        "result": (
            "Resolved the 09:20 retry. Server-6 is reachable and GPU7 has "
            "measured capacity, but the exact M95 checkpoint payload is absent "
            "from allowed storage. Four native capture routes remain blocked and "
            "the supervision axis remains design-only. No queue mutation, "
            "training launch, or native execution occurred."
        ),
        "next_action": (
            "At or after 2026-09-22T10:20:00+08:00, verify the exact M95 "
            "checkpoint payload under allowed storage before resuming the four "
            "frozen native capture routes. Keep referent-supervision-axis in "
            "normal design mode."
        ),
    }
    work["next_action"] = work["last_event_tick"]["next_action"]

    temporary = RESEARCH_WORK.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(work, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, RESEARCH_WORK)
    print(
        json.dumps(
            {
                "report": report_record,
                "decision": decision_record,
                "blocked_ids": list(BLOCKED_IDS),
                "open_id": OPEN_ID,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
