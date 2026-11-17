"""Persist the bounded matcher binding correction on the three due IDs."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_match_cause_binding_20260923-1810.md"
IDS = {
    "referent-supervision-axis": (
        "Derive a distinct expression-level causal supervision unit and "
        "matched native-positive, objectness and listwise controls; native "
        "matcher cause remains unobserved."
    ),
    "referent-discrimination": (
        "When GPU7 is free, verify host/runtime/data/checkpoint and corrected "
        "producer provenance, then run the 256-row opt-in native matcher-cause "
        "capture; reconcile the six outside-seed cases."
    ),
    "instance-identity-representation": (
        "Independently capture query-state vectors for the four same-physical-ID "
        "classes with exact-seed/coordinate and identity controls and a "
        "predeclared rejection rule."
    ),
}


def ref(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    context = json.loads((ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8"))
    assert context["mode"] == "event"
    assert set(context["research_work"]["due_ids"]) == set(IDS)
    assert not context["changes"]["new_terminal_ids"]
    decisions = list((ROOT / "pipeline/decisions").glob("20260923-18*_route_change.md"))
    assert len(decisions) == 1, decisions
    decision = decisions[0].relative_to(ROOT).as_posix()
    refs = [ref(path) for path in (
        REPORT, decision, "scripts/native_manifest_capture_20260922.py",
        "scripts/test_manifest_match_cause_20260923.py",
        "scripts/persist_match_cause_binding_tick_20260923.py",
    )]
    target = ROOT / "pipeline/research_work.json"
    work = json.loads(target.read_text(encoding="utf-8"))
    now = datetime.now().astimezone().isoformat()
    found = set()
    for item in work["candidates"]:
        if item["id"] not in IDS:
            continue
        assert item["stage"] == "diagnosis"
        found.add(item["id"])
        item["next_action"] = IDS[item["id"]]
        item["match_binding_correction_20260923"] = {
            "timestamp": now,
            "report": refs[0],
            "decision": refs[1],
            "synthetic_tests_passed": 15,
            "native_execution_completed": False,
            "admission": False,
        }
        known = {entry["path"]: entry for entry in item["evidence"]}
        for entry in refs:
            if entry["path"] in known:
                if known[entry["path"]]["sha256"] != entry["sha256"]:
                    assert entry["path"] in {
                        "scripts/native_manifest_capture_20260922.py",
                        "scripts/test_manifest_match_cause_20260923.py",
                    }
                    known[entry["path"]]["sha256"] = entry["sha256"]
            else:
                item["evidence"].append(entry)
    assert found == set(IDS)
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = "Three diagnoses remain open; native cause and admission unverified."
    temp = target.with_suffix(".match_binding.tmp")
    with temp.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temp.replace(target)
    print(json.dumps({"report": refs[0], "decision": refs[1], "stages": dict.fromkeys(IDS, "diagnosis")}))


if __name__ == "__main__":
    main()
