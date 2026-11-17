"""Persist one bounded static diagnostic across the three due stable IDs."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDS = {
    "referent-supervision-axis": (
        "Derive a distinct expression-level causal unit and matched native-positive, "
        "any-instance objectness and listwise controls; after opt-in capture, use "
        "the six-row native cause audit without treating target-seed availability "
        "as matcher cause."
    ),
    "referent-discrimination": (
        "When authorized GPU7 capacity is clear, verify host/runtime/data/checkpoint/"
        "producer and run the opt-in 256-row matcher-cause capture; then execute "
        "scripts/m95_exclusion_cause_audit_20260924.py on its capture.json."
    ),
    "instance-identity-representation": (
        "When authorized GPU7 capacity is clear, run the same opt-in query-state "
        "capture, then the preregistered four-scene same-ID analysis with "
        "distinct-ID controls and explicit missing support."
    ),
}
PATHS = (
    "pipeline/reports/m95_exclusion_cause_readiness_20260924-0112.md",
    "pipeline/decisions/20260924-011212_route_change.md",
    "scripts/m95_exclusion_cause_audit_20260924.py",
    "scripts/test_m95_exclusion_cause_audit_20260924.py",
    "scripts/persist_exclusion_cause_tick_20260924.py",
)


def main():
    context = json.loads(
        (ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8")
    )
    assert context["mode"] == "event"
    assert set(context["research_work"]["due_ids"]) == set(IDS)
    refs = [{
        "path": path,
        "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
    } for path in PATHS]
    target = ROOT / "pipeline/research_work.json"
    work = json.loads(target.read_text(encoding="utf-8"))
    now = datetime.now().astimezone().isoformat()
    found = set()
    for candidate in work["candidates"]:
        if candidate["id"] not in IDS:
            continue
        assert candidate["stage"] == "diagnosis"
        found.add(candidate["id"])
        candidate["next_action"] = IDS[candidate["id"]]
        candidate["exclusion_cause_readiness_20260924"] = {
            "timestamp": now, "report": refs[0], "decision": refs[1],
            "cpu_tests_passed": 15, "native_execution_completed": False,
            "admission": False,
        }
        known = {item["path"]: item["sha256"] for item in candidate["evidence"]}
        for item in refs:
            if item["path"] in known:
                assert known[item["path"]] == item["sha256"]
            else:
                candidate["evidence"].append(item)
    assert found == set(IDS)
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = "Three diagnosis tracks remain open; no candidate admission."
    temporary = target.with_suffix(".exclusion_cause.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(target)
    print(json.dumps({"updated": sorted(found), "report": refs[0]}))


if __name__ == "__main__":
    main()
