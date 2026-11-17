"""Persist source-bound partition readiness for the three existing diagnosis IDs."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "pipeline/research_work.json"
REPORT = "pipeline/reports/m95_partition_binding_readiness_20260924-0910.md"
CHECKER = "scripts/m95_exclusion_cause_audit_20260924.py"
TEST = "scripts/test_m95_exclusion_cause_audit_20260924.py"
IDS = {
    "referent-supervision-axis",
    "referent-discrimination",
    "instance-identity-representation",
}


def evidence(path):
    return {
        "path": path,
        "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
    }


def main():
    context = json.loads(
        (ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8")
    )
    if context["mode"] != "event" or set(context["research_work"]["due_ids"]) != IDS:
        raise ValueError("Unexpected tick context")
    work = json.loads(WORK.read_text(encoding="utf-8"))
    refs = [evidence(path) for path in (REPORT, CHECKER, TEST)]
    now = datetime.now().astimezone().isoformat()
    selected = [candidate for candidate in work["candidates"] if candidate["id"] in IDS]
    if len(selected) != len(IDS) or any(c["stage"] != "diagnosis" for c in selected):
        raise ValueError("Diagnosis stage differs")
    for candidate in selected:
        existing = {item["path"]: item["sha256"] for item in candidate["evidence"]}
        if REPORT in existing:
            raise ValueError("Progress already persisted")
        candidate["evidence"].extend(refs)
        candidate["partition_binding_readiness_20260924"] = {
            "timestamp": now,
            "report": refs[0],
            "checker": refs[1],
            "test": refs[2],
            "focused_tests_passed": 21,
            "native_execution_completed": False,
            "admission": False,
        }
        candidate["blocker"] = None
        candidate["retry_after"] = None
        candidate["unblock_condition"] = None
    work["updated_at"] = work["last_event_tick"] = now
    temporary = WORK.with_suffix(".partition-binding.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(WORK)
    print(json.dumps({"report": refs[0], "candidates": sorted(IDS)}))


if __name__ == "__main__":
    main()
