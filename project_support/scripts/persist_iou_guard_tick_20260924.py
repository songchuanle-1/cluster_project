"""Record bounded capture-integrity progress for the three due diagnoses."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDS = {
    "referent-supervision-axis",
    "referent-discrimination",
    "instance-identity-representation",
}
REPORT = "pipeline/reports/m95_iou_guard_readiness_20260924-1408.md"
CHECKER = "scripts/m95_exclusion_cause_audit_20260924.py"
TEST = "scripts/test_m95_exclusion_cause_audit_20260924.py"


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
    assert set(context["research_work"]["due_ids"]) == IDS
    path = ROOT / "pipeline/research_work.json"
    work = json.loads(path.read_text(encoding="utf-8"))
    now = datetime.now().astimezone().isoformat()
    report, checker, test = map(ref, (REPORT, CHECKER, TEST))
    found = set()
    for candidate in work["candidates"]:
        if candidate["id"] not in IDS:
            continue
        assert candidate["stage"] == "diagnosis"
        found.add(candidate["id"])
        candidate["iou_guard_readiness_20260924"] = {
            "timestamp": now,
            "report": report,
            "checker": checker,
            "test": test,
            "tests_passed": 35,
            "native_execution_completed": False,
            "admission": False,
            "blocker": "External PID 3694608 occupies 41,996 MiB on authorized GPU7",
            "unblock_condition": candidate["unblock_condition"],
            "next_action": candidate["next_action"],
        }
        if not any(item["path"] == REPORT for item in candidate["evidence"]):
            candidate["evidence"].append(report)
    assert found == IDS
    work["updated_at"] = work["last_event_tick"] = now
    temporary = path.with_suffix(".iou_guard.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(path)
    print(json.dumps({"updated": sorted(found), "report": report}))


if __name__ == "__main__":
    main()
