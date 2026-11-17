"""Attach the bounded cause audit to the three existing diagnosis tracks."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_supervision_cause_boundary_20260924-0014.json"
DECISION = "pipeline/decisions/20260924-001532_route_change.md"
NEXT = {
    "referent-supervision-axis": (
        "On the fixed six exclusion scenes, distinguish target-seed availability "
        "from native matcher cause. Derive a distinct expression-level causal "
        "unit and matched native-positive, any-instance objectness and listwise "
        "controls; no relabeling-only or deduplication successor."
    ),
    "referent-discrimination": (
        "When authorized GPU7 is free, verify host/runtime/data/checkpoint/producer "
        "and run the opt-in 256-row native matcher-cause capture. Classify the six "
        "outside-seed positives by nearest-GT versus instance membership."
    ),
    "instance-identity-representation": (
        "When authorized GPU7 is free, run the same opt-in query-state capture, "
        "then the preregistered four-scene same-ID analysis with distinct-ID "
        "controls and explicit missing support."
    ),
}


def ref(path):
    return {
        "path": path,
        "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
    }


def main():
    context = json.loads(
        (ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8")
    )
    assert context["mode"] == "event"
    assert set(context["research_work"]["due_ids"]) == set(NEXT)
    report = json.loads((ROOT / REPORT).read_text(encoding="utf-8"))
    groups = report["groups"]
    exclusion = groups["recoverable_positive_set_excludes_acceptable"]
    assert exclusion["expressions"] == 6
    assert exclusion["target_seed_selector_available"] == 1
    assert exclusion["rows_with_saved_outside_seed_positive"] == 3
    assert report["admission"] is False and report["native_execution_completed"] is False
    refs = [ref(path) for path in (
        REPORT, DECISION, "scripts/m95_supervision_cause_boundary_20260924.py",
        "scripts/test_m95_supervision_cause_boundary_20260924.py",
        "scripts/persist_supervision_cause_boundary_tick_20260924.py",
    )]
    target = ROOT / "pipeline/research_work.json"
    work = json.loads(target.read_text(encoding="utf-8"))
    now = datetime.now().astimezone().isoformat()
    found = set()
    for candidate in work["candidates"]:
        if candidate["id"] not in NEXT:
            continue
        assert candidate["stage"] == "diagnosis"
        found.add(candidate["id"])
        candidate["next_action"] = NEXT[candidate["id"]]
        candidate["cause_boundary_20260924"] = {
            "timestamp": now, "report": refs[0], "decision": refs[1],
            "cpu_tests_passed": 5, "native_execution_completed": False,
            "admission": False,
        }
        known = {item["path"]: item["sha256"] for item in candidate["evidence"]}
        for item in refs:
            if item["path"] in known:
                assert known[item["path"]] == item["sha256"]
            else:
                candidate["evidence"].append(item)
    assert found == set(NEXT)
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = "Three diagnosis tracks remain open; no candidate admission."
    temporary = target.with_suffix(".cause_boundary.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(target)
    print(json.dumps({"updated": sorted(found), "report": refs[0]}))


if __name__ == "__main__":
    main()
