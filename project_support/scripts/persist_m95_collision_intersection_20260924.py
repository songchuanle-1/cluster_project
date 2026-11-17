"""Persist this tick's bounded diagnostic progress without admitting a model."""

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
REPORT = "pipeline/reports/m95_collision_binding_intersection_20260924-1511.md"
OLD = {
    CHECKER: "59ab599b57b405eb64ca4216d6ac162da3073650555196c7f259ccc13e8dff33",
    TEST: "3d8b6e2251d6c65b0e3a8ee383d64437ac1c421939593dab03eee740daae1cf5",
}


def reference(path):
    return {
        "path": path,
        "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
    }


def main():
    import sys

    if len(sys.argv) != 2:
        raise ValueError("Expected the logged decision's relative path")
    decision = sys.argv[1].replace("\\", "/")
    if not decision.startswith("pipeline/decisions/"):
        raise ValueError("Decision must be project-local")
    context = json.loads(
        (ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8")
    )
    if context["mode"] != "design" or set(context["research_work"]["due_ids"]) != DUE:
        raise ValueError("Unexpected design preflight")
    original = WORK.read_bytes()
    queue_hash = reference("pipeline/queue.json")["sha256"]
    work = json.loads(original)
    refs = {path: reference(path) for path in (CHECKER, TEST, REPORT, decision)}
    now = datetime.now().astimezone()
    found = set()
    affected = set()
    for candidate in work["candidates"]:
        evidence = candidate.get("evidence", [])
        for item in evidence:
            path = item["path"]
            full = Path(path) if Path(path).is_absolute() else ROOT / path
            full = full.resolve()
            if not full.is_relative_to(ROOT.resolve()) or not full.is_file():
                raise ValueError("Missing or out-of-project evidence: " + path)
            actual = hashlib.sha256(full.read_bytes()).hexdigest()
            if actual != item["sha256"]:
                if path not in OLD or item["sha256"] != OLD[path]:
                    raise ValueError("Unrelated evidence drift: " + path)
                archive = candidate.setdefault("superseded_source_evidence", [])
                archived = {
                    "path": path, "sha256": item["sha256"],
                    "reason": "Source subsequently edited; historical bytes unavailable locally",
                    "superseded_by_sha256": actual, "not_current_proof": True,
                }
                if archived not in archive:
                    archive.append(archived)
                item["sha256"] = actual
                affected.add(candidate["id"])
        if candidate["id"] not in DUE:
            continue
        if candidate["stage"] not in ("diagnosis", "blocked"):
            raise ValueError("Unexpected due stage")
        found.add(candidate["id"])
        for ref in refs.values():
            if ref not in evidence:
                evidence.append(ref)
        candidate["collision_binding_intersection_20260924"] = {
            "timestamp": now.isoformat(),
            "report": refs[REPORT],
            "checker": refs[CHECKER],
            "test": refs[TEST],
            "decision": refs[decision],
            "tests_passed": 34,
            "native_execution_completed": False,
            "admission": False,
            "blocker": "External PID 3694608 occupies 41,996 MiB on authorized GPU7",
            "unblock_condition": (
                "Authorized GPU7 clears and SSH/runtime/data/checkpoint/producer "
                "provenance and actual memory/occupancy are verified."
            ),
        }
        candidate["blocker"] = candidate["collision_binding_intersection_20260924"]["blocker"]
        candidate["stage"] = "blocked"
        candidate["retry_after"] = (now + timedelta(minutes=20)).isoformat()
        candidate["unblock_condition"] = candidate[
            "collision_binding_intersection_20260924"
        ]["unblock_condition"]
        candidate["alternatives_attempted"] = (
            "One read-only GPU7 query; bounded CPU synthetic intersection test "
            "and existing matcher/binding controls, 34 tests passed."
        )
    if found != DUE:
        raise ValueError("Missing due IDs or expected evidence update")
    work["design_cycle"] = {
        "timestamp": now.isoformat(),
        "stop_reason": "external_resource_blocked",
        "attempted_ids": sorted(DUE),
        "evidence": [refs[REPORT], refs[CHECKER], refs[TEST], refs[decision]],
        "resume_condition": (
            "At or after the candidate retry time, recheck authorized GPU7. "
            "When clear, verify runtime/data/checkpoint/producer and run one "
            "ordered native capture, then the six-row and four-scene controls."
        ),
    }
    work["updated_at"] = now.isoformat()
    work["last_event_tick"] = now.isoformat()
    if WORK.read_bytes() != original or reference("pipeline/queue.json")["sha256"] != queue_hash:
        raise ValueError("Concurrent research or queue change")
    temp = WORK.with_suffix(".collision_intersection.tmp")
    with temp.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    os.replace(temp, WORK)
    print(json.dumps({"due_ids": sorted(found), "affected_ids": sorted(affected),
                      "report_sha256": refs[REPORT]["sha256"],
                      "queue_sha256": queue_hash}))


if __name__ == "__main__":
    main()
