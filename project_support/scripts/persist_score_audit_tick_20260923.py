"""Persist the bounded score audit against the three existing diagnosis IDs."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_discordance_score_audit_20260923-1307.json"
DECISION = "pipeline/decisions/20260923-131241_route_change.md"
NEXT = {
    "referent-supervision-axis": (
        "The same-mask positive/negative score pattern does not identify a distinct "
        "supervision unit. Formulate an independently testable expression-level "
        "target with native-positive and objectness matched controls; reject generic "
        "mask relabeling/ranking and require native backward/resources before admission."
    ),
    "referent-discrimination": (
        "Preserve target26/peer5/outside-registered-peers1 strata and the six "
        "unattributed outside-seed positives. Specify an independent physical "
        "coordinate/cause test for a falsifiable discrimination mechanism before "
        "changing selection; no inference from score direction alone."
    ),
    "instance-identity-representation": (
        "Distinct logits and mostly positive-higher scores refute binary-mask "
        "equality as a state-collapse test. Specify a query-state capture with "
        "seed/identity-matched controls and a predeclared rejection threshold "
        "only if an independent representation mechanism is derived."
    ),
}


def ref(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    context = json.loads((ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8"))
    result = json.loads((ROOT / REPORT).read_text(encoding="utf-8"))
    target = ROOT / "pipeline/research_work.json"
    work = json.loads(target.read_text(encoding="utf-8"))
    assert context["mode"] == "event" and set(context["research_work"]["due_ids"]) == set(NEXT)
    assert result["contract"] == "m95_static_discordance_score_audit_v1"
    assert result["groups"]["all"]["positive_higher"] == 29
    assert result["groups"]["acceptable"]["positive_higher"] == 22
    assert result["groups"]["positive_outside_seed"]["positive_higher"] == 6
    assert not result["admission"] and not result["queue_mutation"]
    assert result["evidence"][0] == ref(result["evidence"][0]["path"])
    now = datetime.now().astimezone().isoformat()
    refs = [ref(p) for p in (
        REPORT, DECISION, "scripts/m95_discordance_score_audit_20260923.py",
        "scripts/test_m95_discordance_score_audit_20260923.py", __file__,
    )]
    found = set()
    for candidate in work["candidates"]:
        if candidate["id"] not in NEXT:
            continue
        found.add(candidate["id"])
        assert candidate["stage"] == "diagnosis"
        candidate["next_action"] = NEXT[candidate["id"]]
        candidate["score_audit_completed_20260923"] = {
            "timestamp": now,
            "report": ref(REPORT),
            "decision": ref(DECISION),
            "static_analysis_completed": True,
            "admission": False,
            "native_backward_executed": False,
        }
        known = {item["path"]: item["sha256"] for item in candidate["evidence"]}
        for item in refs:
            if item["path"] in known:
                assert known[item["path"]] == item["sha256"]
            else:
                candidate["evidence"].append(item)
    assert found == set(NEXT)
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = (
        "Three diagnosis IDs retain distinct falsifiable mechanism/control tasks; "
        "no candidate is admitted from same-mask score direction."
    )
    temporary = target.with_suffix(".score_audit.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(target)
    print(json.dumps({"report": ref(REPORT), "decision": ref(DECISION), "stages": found and dict.fromkeys(NEXT, "diagnosis")}))


if __name__ == "__main__":
    main()
