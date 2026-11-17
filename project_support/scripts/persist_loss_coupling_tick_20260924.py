"""Attach the bounded source audit to the existing diagnosis tracks."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_supervision_loss_coupling_20260924-0210.md"
DECISION = "pipeline/decisions/20260924-021124_route_change.md"
IDS = {
    "referent-supervision-axis",
    "referent-discrimination",
    "instance-identity-representation",
}


def main():
    context = json.loads(
        (ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8")
    )
    assert context["mode"] == "event"
    assert set(context["research_work"]["due_ids"]) == IDS
    refs = [
        {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
        for path in (REPORT, DECISION)
    ]
    target = ROOT / "pipeline/research_work.json"
    work = json.loads(target.read_text(encoding="utf-8"))
    now = datetime.now().astimezone().isoformat()
    found = set()
    for candidate in work["candidates"]:
        if candidate["id"] not in IDS:
            continue
        assert candidate["stage"] == "diagnosis"
        found.add(candidate["id"])
        known = {item["path"]: item["sha256"] for item in candidate["evidence"]}
        for item in refs:
            if item["path"] in known:
                assert known[item["path"]] == item["sha256"]
            else:
                candidate["evidence"].append(item)
        candidate["loss_coupling_contract_20260924"] = {
            "timestamp": now,
            "report": refs[0],
            "decision": refs[1],
            "native_execution_completed": False,
            "admission": False,
        }
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "After native cause capture, implement the component-isolated and "
                "coupled same-forward controls in the loss-coupling audit; require "
                "an expression-level unit distinct from native-positive relabeling "
                "and listwise ranking before candidate design."
            )
    assert found == IDS
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = "Resume three stable diagnosis IDs; no candidate admission."
    temporary = target.with_suffix(".loss_coupling.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(target)
    print(json.dumps({"updated": sorted(found), "report": refs[0]}))


if __name__ == "__main__":
    main()
