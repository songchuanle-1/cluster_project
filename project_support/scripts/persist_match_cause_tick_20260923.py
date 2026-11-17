"""Persist the source-bound diagnostic contract on the three due work IDs."""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_match_cause_contract_20260923-1610.md"
DECISION = sys.argv[1] if len(sys.argv) == 2 else None
IDS = {
    "referent-supervision-axis":
        "Derive an expression-level causal supervision unit and matched native-positive, objectness and listwise controls; native matcher cause is not yet captured. Only then assess native backward/resources.",
    "referent-discrimination":
        "On free server-6 GPU7, capture criterion-bound sampled coordinates, GT centroids and per-GT nearest/membership causes on the frozen manifest; validate with the independent CPU contract before interpreting six outside-seed positives.",
    "instance-identity-representation":
        "Independently capture query-state vectors for the four same-physical-ID classes with exact seed-index/coordinate and physical-identity controls and a predeclared rejection rule; matcher geometry alone cannot establish state collapse.",
}


def ref(path):
    return {
        "path": path,
        "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
    }


def main():
    assert DECISION and DECISION.startswith("pipeline/decisions/") and DECISION.endswith("_route_change.md")
    context = json.loads((ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8"))
    assert context["mode"] == "event" and not context["changes"]["new_terminal_ids"]
    assert set(context["research_work"]["due_ids"]) == set(IDS)
    target = ROOT / "pipeline/research_work.json"
    work = json.loads(target.read_text(encoding="utf-8"))
    paths = [
        REPORT, DECISION, "scripts/m95_match_cause_contract_20260923.py",
        "scripts/test_m95_match_cause_contract_20260923.py",
    ]
    refs = [ref(path) for path in paths]
    now = datetime.now().astimezone().isoformat()
    found = set()
    for item in work["candidates"]:
        if item["id"] not in IDS:
            continue
        assert item["stage"] == "diagnosis"
        found.add(item["id"])
        item["next_action"] = IDS[item["id"]]
        item["match_cause_contract_20260923"] = {
            "timestamp": now,
            "report": refs[0],
            "decision": refs[1],
            "synthetic_tests_passed": 5,
            "native_execution_completed": False,
            "admission": False,
        }
        known = {entry["path"]: entry["sha256"] for entry in item["evidence"]}
        for evidence in refs:
            if evidence["path"] in known:
                assert known[evidence["path"]] == evidence["sha256"]
            else:
                item["evidence"].append(evidence)
    assert found == set(IDS)
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = "Three diagnosis tracks remain open; native cause and candidate admission unverified."
    temp = target.with_suffix(".match_cause.tmp")
    with temp.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temp.replace(target)
    print(json.dumps({"report": refs[0], "decision": refs[1], "stages": dict.fromkeys(IDS, "diagnosis")}))


if __name__ == "__main__":
    main()
