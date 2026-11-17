"""Persist bounded producer-provenance progress for the three due research IDs."""

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "pipeline/research_work.json"
QUEUE = ROOT / "pipeline/queue.json"
DUE = {
    "referent-supervision-axis",
    "referent-discrimination",
    "instance-identity-representation",
}
CHECKER = "scripts/m95_exclusion_cause_audit_20260924.py"
TEST = "scripts/test_m95_exclusion_cause_audit_20260924.py"
REPORT = "pipeline/reports/m95_producer_provenance_guard_20260924-1611.md"
DECISION = "pipeline/decisions/20260924-161132_route_change.md"
OLD = {
    CHECKER: "d81f32a152b7425a2b03c3452fb358f12dd59f93e0135abd10e13bde98407ad3",
    TEST: "941d9b46a3a08576770a66cb03fb1dea1458426177b50b720cb88c9e154ffb2c",
}


def reference(path):
    return {
        "path": path,
        "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
    }


def main():
    context = json.loads(
        (ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8")
    )
    if context["mode"] != "design" or set(context["research_work"]["due_ids"]) != DUE:
        raise ValueError("Unexpected design preflight")
    original = WORK.read_bytes()
    queue_hash = reference("pipeline/queue.json")["sha256"]
    work = json.loads(original)
    refs = {path: reference(path) for path in (CHECKER, TEST, REPORT, DECISION)}
    now = datetime.now().astimezone()
    found = set()
    for candidate in work["candidates"]:
        evidence = candidate.get("evidence", [])
        for item in evidence:
            path = item["path"]
            full = (Path(path) if Path(path).is_absolute() else ROOT / path).resolve()
            if not full.is_relative_to(ROOT.resolve()) or not full.is_file():
                raise ValueError("Missing or out-of-project evidence: " + path)
            actual = hashlib.sha256(full.read_bytes()).hexdigest()
            if actual == item["sha256"]:
                continue
            if path not in OLD or item["sha256"] != OLD[path]:
                raise ValueError("Unrelated evidence drift: " + path)
            archive = candidate.setdefault("superseded_source_evidence", [])
            archived = {
                "path": path,
                "sha256": item["sha256"],
                "reason": "Source subsequently edited; historical bytes unavailable locally",
                "superseded_by_sha256": actual,
                "not_current_proof": True,
            }
            if archived not in archive:
                archive.append(archived)
            item["sha256"] = actual
        if candidate["id"] not in DUE:
            continue
        if candidate["stage"] not in ("diagnosis", "blocked"):
            raise ValueError("Unexpected due stage")
        found.add(candidate["id"])
        for ref in refs.values():
            if ref not in evidence:
                evidence.append(ref)
        blocker = "External PID 3694608 occupies 41,996 MiB on authorized GPU7"
        condition = (
            "Authorized GPU7 clears and SSH/runtime/data/checkpoint/producer "
            "provenance and actual memory/occupancy are verified."
        )
        candidate["producer_provenance_guard_20260924"] = {
            "timestamp": now.isoformat(),
            "report": refs[REPORT],
            "checker": refs[CHECKER],
            "test": refs[TEST],
            "decision": refs[DECISION],
            "tests_passed": 38,
            "native_execution_completed": False,
            "admission": False,
            "blocker": blocker,
            "unblock_condition": condition,
        }
        candidate["blocker"] = blocker
        candidate["stage"] = "blocked"
        candidate["retry_after"] = (now + timedelta(minutes=20)).isoformat()
        candidate["unblock_condition"] = condition
        candidate["alternatives_attempted"] = (
            "One read-only GPU7 query; local producer-hash guard and 38 focused "
            "synthetic tests. No native execution or unauthorized host."
        )
    if found != DUE:
        raise ValueError("Missing due IDs")
    work["design_cycle"] = {
        "timestamp": now.isoformat(),
        "stop_reason": "external_resource_blocked",
        "attempted_ids": sorted(DUE),
        "evidence": list(refs.values()),
        "resume_condition": (
            "At or after candidate retry time, recheck authorized GPU7. When "
            "clear, verify runtime/data/checkpoint/producer and run one ordered "
            "256-row native capture, then six-row and four-scene controls."
        ),
    }
    work["updated_at"] = now.isoformat()
    work["last_event_tick"] = now.isoformat()
    if WORK.read_bytes() != original or reference("pipeline/queue.json")["sha256"] != queue_hash:
        raise ValueError("Concurrent research or queue change")
    temp = WORK.with_suffix(".producer_guard.tmp")
    with temp.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    os.replace(temp, WORK)
    print(json.dumps({"due_ids": sorted(found), "queue_sha256": queue_hash}))


if __name__ == "__main__":
    main()
