"""Persist the bounded identity-query contract on the existing diagnosis IDs."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_identity_query_contract_20260923-1915.md"
DECISION = "pipeline/decisions/20260923-191357_route_change.md"
SOURCE = "scripts/native_manifest_capture_20260922.py"
TEST = "scripts/test_manifest_identity_query_20260923.py"
IDS = {
    "referent-supervision-axis": (
        "Derive a distinct expression-level causal supervision unit with "
        "matched native-positive, objectness and listwise controls; native "
        "matcher cause remains unobserved."
    ),
    "referent-discrimination": (
        "When GPU7 is free, verify host/runtime/data/checkpoint and corrected "
        "producer provenance, then run the frozen 256-row opt-in native "
        "matcher-cause capture and reconcile six outside-seed cases."
    ),
    "instance-identity-representation": (
        "When GPU7 is free, run the same frozen 256-row capture with matcher "
        "causes and identity query states; analyze four same-physical-ID "
        "classes using coordinate, cause and distinct-ID controls."
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
    assert set(context["research_work"]["due_ids"]) == set(IDS)
    assert not context["changes"]["new_terminal_ids"]
    refs = [ref(path) for path in (REPORT, DECISION, SOURCE, TEST)]
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
        item["identity_query_contract_20260923"] = {
            "timestamp": now,
            "report": refs[0],
            "decision": refs[1],
            "cpu_tests_passed": 18,
            "native_execution_completed": False,
            "admission": False,
        }
        known = {entry["path"]: entry for entry in item["evidence"]}
        for entry in refs:
            if entry["path"] in known:
                if known[entry["path"]]["sha256"] != entry["sha256"]:
                    assert entry["path"] == SOURCE
                    known[entry["path"]]["sha256"] = entry["sha256"]
            else:
                item["evidence"].append(entry)
    assert found == set(IDS)
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = (
        "Three diagnoses remain open; native matcher cause and query-state "
        "capture, mechanism admission and resources are unverified."
    )
    temp = target.with_suffix(".identity_query.tmp")
    with temp.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temp.replace(target)
    print(json.dumps({"evidence": refs, "stages": dict.fromkeys(IDS, "diagnosis")}))


if __name__ == "__main__":
    main()
