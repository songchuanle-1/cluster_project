"""Attach bounded partition evidence to existing research IDs."""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDS = {
    "referent-supervision-axis":
        "Derive a distinct expression-level causal supervision unit and matched native-positive, any-instance objectness and listwise controls; the fixed partition is descriptive only.",
    "referent-discrimination":
        "When authorized GPU7 is free, verify runtime/data/checkpoint/producer hashes and run the opt-in 256-row native matcher-cause capture; classify six outside-seed classes.",
    "instance-identity-representation":
        "When authorized GPU7 is free, run the same opt-in query-state capture, then the preregistered four-scene same-ID analysis with distinct-ID controls and missing support.",
}


def evidence(path):
    return {
        "path": path,
        "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
    }


def main():
    decision = sys.argv[1]
    context = json.loads(
        (ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8")
    )
    assert context["mode"] == "event"
    assert set(context["research_work"]["due_ids"]) == set(IDS)
    refs = [evidence(path) for path in (
        "pipeline/reports/m95_supervision_partition_controls_20260923-2315.json",
        decision,
        "scripts/m95_supervision_partition_controls_20260923.py",
        "scripts/test_m95_supervision_partition_controls_20260923.py",
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
        item["partition_controls_20260923"] = {
            "timestamp": now,
            "report": refs[0],
            "decision": refs[1],
            "cpu_tests_passed": 5,
            "native_execution_completed": False,
            "admission": False,
        }
        known = {entry["path"]: entry["sha256"] for entry in item["evidence"]}
        for ref in refs:
            if ref["path"] in known:
                assert known[ref["path"]] == ref["sha256"], ref["path"]
            else:
                item["evidence"].append(ref)
    assert found == set(IDS)
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = "Three diagnosis IDs remain open; no candidate admission."
    temp = target.with_suffix(".partition.tmp")
    with temp.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temp.replace(target)
    print(json.dumps({"updated": sorted(found), "report": refs[0]}))


if __name__ == "__main__":
    main()
