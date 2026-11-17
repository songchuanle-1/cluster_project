"""Persist the bounded frozen-geometry diagnosis on existing work IDs."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_geometry_source_audit_20260923-1507.md"
DECISION = "pipeline/decisions/20260923-151833_route_change.md"
IDS = {
    "referent-supervision-axis": (
        "Specify a genuinely expression-level supervision unit and matched "
        "native-positive, objectness and listwise controls; hierarchy positions "
        "cannot establish the native match cause. Test native backward/resources "
        "only after scientific admission."
    ),
    "referent-discrimination": (
        "Capture independently bound native sampled superpoint coordinates, "
        "GT centroids and matcher-cause tags for the frozen strata when GPU7 is "
        "available. Do not substitute hierarchical FPS positions."
    ),
    "instance-identity-representation": (
        "Specify an independent query-state capture with exact-seed and "
        "physical-identity controls and a predeclared rejection threshold; "
        "hierarchical positions do not bind query states."
    ),
}


def ref(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    context = json.loads((ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8"))
    assert context["mode"] == "event" and set(context["research_work"]["due_ids"]) == set(IDS)
    assert not context["changes"]["new_terminal_ids"]
    target = ROOT / "pipeline/research_work.json"
    work = json.loads(target.read_text(encoding="utf-8"))
    refs = [ref(p) for p in (REPORT, DECISION, "scripts/persist_geometry_source_tick_20260923.py")]
    now = datetime.now().astimezone().isoformat()
    found = set()
    for item in work["candidates"]:
        if item["id"] not in IDS:
            continue
        assert item["stage"] == "diagnosis"
        found.add(item["id"])
        item["next_action"] = IDS[item["id"]]
        item["geometry_source_audit_20260923"] = {
            "timestamp": now,
            "report": refs[0],
            "decision": refs[1],
            "native_execution_completed": False,
            "admission": False,
        }
        known = {e["path"]: e["sha256"] for e in item["evidence"]}
        for evidence in refs:
            if evidence["path"] in known:
                assert known[evidence["path"]] == evidence["sha256"]
            else:
                item["evidence"].append(evidence)
    assert found == set(IDS)
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = "Three diagnosis tracks remain open; native cause and candidate admission unverified."
    temp = target.with_suffix(".geometry_source.tmp")
    with temp.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temp.replace(target)
    print(json.dumps({"report": refs[0], "decision": refs[1], "stages": dict.fromkeys(IDS, "diagnosis")}))


if __name__ == "__main__":
    main()
