"""Attach the source-bound mask-indexing audit to the three stable diagnosis IDs."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_repeated_gt_mask_contract_20260924-0309.json"
DECISION = "pipeline/decisions/20260924-031039_route_change.md"
SCRIPT = "scripts/m95_repeated_gt_mask_contract_20260924.py"
TEST = "scripts/test_m95_repeated_gt_mask_contract_20260924.py"
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
        for path in (REPORT, DECISION, SCRIPT, TEST)
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
        candidate["repeated_gt_mask_contract_20260924"] = {
            "timestamp": now,
            "report": refs[0],
            "decision": refs[1],
            "tests_passed": 20,
            "native_execution_completed": False,
            "admission": False,
        }
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Once authorized GPU7 is clear, capture the native 256-row GT "
                "matcher bindings. Quantify repeated-GT mask-index mismatches "
                "on matched TRAIN forwards before component-isolated versus "
                "coupled controls; require a distinct expression-level unit."
            )
        elif candidate["id"] == "referent-discrimination":
            candidate["next_action"] = (
                "When authorized GPU7 capacity is clear, verify host/runtime/"
                "data/checkpoint/producer, run the opt-in 256-row matcher-cause "
                "capture, audit GT-mask binding, then execute the six-row "
                "exclusion-cause checker."
            )
        else:
            candidate["next_action"] = (
                "When authorized GPU7 capacity is clear, run the same opt-in "
                "matcher-cause/query-state capture with GT-mask binding, then "
                "the preregistered four-scene same-ID/distinct-ID analysis."
            )
    assert found == IDS
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = "Resume native capture on the three stable diagnosis IDs after occupancy clears."
    temporary = target.with_suffix(".repeated_gt_mask.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(target)
    print(json.dumps({"updated": sorted(found), "report": refs[0]}))


if __name__ == "__main__":
    main()
