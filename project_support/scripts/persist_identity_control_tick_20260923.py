"""Persist this event's bounded evidence on existing diagnosis IDs."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATHS = (
    "pipeline/reports/m95_identity_query_control_readiness_20260923-2024.md",
    "pipeline/decisions/20260923-202544_route_change.md",
    "scripts/m95_identity_query_controls_20260923.py",
    "scripts/test_m95_identity_query_controls_20260923.py",
)
NEXT = {
    "referent-supervision-axis": (
        "Derive a distinct expression-level causal supervision unit with matched "
        "native-positive, objectness and listwise controls; do not repackage "
        "exact-mask discordance as a new loss."
    ),
    "referent-discrimination": (
        "On free authorized GPU7, verify runtime/data/checkpoint and producer "
        "hashes; execute 256-row opt-in matcher-cause capture, then classify "
        "the six outside-seed discordant classes."
    ),
    "instance-identity-representation": (
        "On free authorized GPU7, run the same 256-row opt-in query-state capture "
        "and execute the preregistered four-scene paired analysis with matched "
        "distinct-ID controls; report absent support."
    ),
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
    assert set(context["research_work"]["due_ids"]) == set(NEXT)
    assert not context["changes"]["new_terminal_ids"]
    refs = [reference(path) for path in PATHS]
    target = ROOT / "pipeline/research_work.json"
    work = json.loads(target.read_text(encoding="utf-8"))
    now = datetime.now().astimezone().isoformat()
    found = set()
    for item in work["candidates"]:
        if item["id"] not in NEXT:
            continue
        assert item["stage"] == "diagnosis"
        found.add(item["id"])
        item["next_action"] = NEXT[item["id"]]
        item["identity_control_readiness_20260923"] = {
            "timestamp": now,
            "report": refs[0],
            "decision": refs[1],
            "analysis": refs[2],
            "test": refs[3],
            "cpu_tests_passed": 23,
            "native_execution_completed": False,
            "admission": False,
        }
        known = {entry["path"]: entry for entry in item["evidence"]}
        for entry in refs:
            if entry["path"] not in known:
                item["evidence"].append(entry)
            else:
                assert known[entry["path"]]["sha256"] == entry["sha256"]
    assert found == set(NEXT)
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = (
        "Three diagnosis IDs remain open; native capture, mechanism admission "
        "and resources are unverified."
    )
    temp = target.with_suffix(".identity_control.tmp")
    with temp.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temp.replace(target)
    print(json.dumps({"evidence": refs, "stages": dict.fromkeys(NEXT, "diagnosis")}))


if __name__ == "__main__":
    main()
