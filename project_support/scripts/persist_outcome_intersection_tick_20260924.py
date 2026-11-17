"""Record a bounded static advance on the three existing diagnosis IDs."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_outcome_intersection_readiness_20260924-1310.md"
PATHS = (
    REPORT,
    "scripts/m95_exclusion_cause_audit_20260924.py",
    "scripts/test_m95_exclusion_cause_audit_20260924.py",
)
IDS = {
    "referent-supervision-axis",
    "referent-discrimination",
    "instance-identity-representation",
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
    assert context["mode"] == "event"
    assert set(context["research_work"]["due_ids"]) == IDS
    assert not context["changes"]["new_terminal_ids"]
    refs = [reference(path) for path in PATHS]
    target = ROOT / "pipeline/research_work.json"
    work = json.loads(target.read_text(encoding="utf-8"))
    now = datetime.now().astimezone().isoformat()
    found = set()
    for item in work["candidates"]:
        if item["id"] not in IDS:
            continue
        assert item["stage"] == "diagnosis"
        found.add(item["id"])
        item["outcome_intersection_readiness_20260924"] = {
            "timestamp": now,
            "report": refs[0],
            "checker": refs[1],
            "test": refs[2],
            "tests_passed": 26,
            "native_execution_completed": False,
            "admission": False,
        }
        known = {entry["path"]: entry for entry in item["evidence"]}
        for entry in refs:
            if entry["path"] in known:
                known[entry["path"]]["sha256"] = entry["sha256"]
            else:
                item["evidence"].append(entry)
        item["blocker"] = "External GPU7 job occupies 41,996 MiB"
        item["unblock_condition"] = (
            "Authorized GPU7 capacity clears and SSH/runtime/data/checkpoint "
            "provenance and actual memory/occupancy are verified."
        )
    assert found == IDS
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = (
        "Run opt-in ordered 256-row native capture when GPU7 and runtime gates "
        "pass; then check frozen outcomes, GT-mask binding, six-row exclusion "
        "causes and four-scene identity controls."
    )
    temporary = target.with_suffix(".outcome_intersection.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(target)
    print(json.dumps({"updated": sorted(found), "report": refs[0]}))


if __name__ == "__main__":
    main()
