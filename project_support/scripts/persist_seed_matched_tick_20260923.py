"""Persist frozen seed-matched diagnosis on the existing three work IDs."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_seed_matched_audit_20260923-1410.json"
DECISION = "pipeline/decisions/20260923-141207_route_change.md"
NEXT = {
    "referent-supervision-axis": (
        "Four same-physical-seed-ID discordant mask classes retain positive-higher "
        "scores, with zero exact seed-index pairs. Define an expression-level "
        "supervision unit distinguishable from native-positive relabeling and "
        "objectness/listwise controls; native backward and resources remain required."
    ),
    "referent-discrimination": (
        "Only four discordant classes match physical seed identity across labels, "
        "none at exact seed index. Preserve target/peer/outside strata and obtain "
        "independent coordinate and nearest-GT cause evidence before a physical "
        "discrimination mechanism; do not infer class identity from outside peers."
    ),
    "instance-identity-representation": (
        "The four same-instance-seed-ID classes are not exact seed-index matches "
        "and their logits/scores differ. Specify independent query-state capture "
        "with exact-seed and physical-identity controls plus a predeclared "
        "rejection threshold before claiming representation collapse."
    ),
}


def ref(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    context = json.loads((ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8"))
    report = json.loads((ROOT / REPORT).read_text(encoding="utf-8"))
    assert context["mode"] == "event" and set(context["research_work"]["due_ids"]) == set(NEXT)
    assert report["contract"] == "m95_static_seed_matched_audit_v1"
    assert report["summary"]["matched_classes"] == 4
    assert report["summary"]["exact_seed_index_pairs"] == 0
    assert not report["admission"] and not report["queue_mutation"]
    assert report["evidence"][0] == ref(report["evidence"][0]["path"])
    target = ROOT / "pipeline/research_work.json"
    work = json.loads(target.read_text(encoding="utf-8"))
    refs = [ref(p) for p in (
        REPORT, DECISION, "scripts/m95_seed_matched_audit_20260923.py",
        "scripts/test_m95_seed_matched_audit_20260923.py", "scripts/persist_seed_matched_tick_20260923.py",
    )]
    now = datetime.now().astimezone().isoformat()
    found = set()
    for candidate in work["candidates"]:
        if candidate["id"] not in NEXT:
            continue
        found.add(candidate["id"])
        assert candidate["stage"] == "diagnosis"
        candidate["next_action"] = NEXT[candidate["id"]]
        candidate["seed_matched_completed_20260923"] = {
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
    work["next_action"] = "Three bounded diagnosis tracks remain open; no candidate passes admission."
    temporary = target.with_suffix(".seed_matched.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(target)
    print(json.dumps({"report": ref(REPORT), "decision": ref(DECISION), "stages": dict.fromkeys(NEXT, "diagnosis")}))


if __name__ == "__main__":
    main()
