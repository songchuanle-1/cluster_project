"""Persist bounded static validation on the three due diagnosis candidates."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "pipeline/research_work.json"
DUE = {
    "referent-supervision-axis",
    "referent-discrimination",
    "instance-identity-representation",
}
PATHS = (
    "pipeline/reports/m95_all_row_outcome_guard_20260924-0610.md",
    "scripts/m95_exclusion_cause_audit_20260924.py",
    "scripts/test_m95_exclusion_cause_audit_20260924.py",
)


def reference(path):
    return {
        "path": path,
        "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
    }


def main():
    context = json.loads(
        (ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8")
    )
    if context["mode"] != "event" or set(context["research_work"]["due_ids"]) != DUE:
        raise ValueError("Unexpected tick mode or due candidate IDs")
    work = json.loads(WORK.read_text(encoding="utf-8"))
    refs = [reference(path) for path in PATHS]
    now = datetime.now().astimezone().isoformat()
    found = set()
    for candidate in work["candidates"]:
        if candidate["id"] not in DUE:
            continue
        if candidate["stage"] != "diagnosis":
            raise ValueError("Unexpected research stage")
        found.add(candidate["id"])
        candidate["all_row_outcome_guard_20260924"] = {
            "timestamp": now,
            "report": refs[0],
            "checker": refs[1],
            "test": refs[2],
            "tests_passed": 24,
            "native_execution_completed": False,
            "admission": False,
        }
        evidence = candidate.setdefault("evidence", [])
        for ref in refs:
            old = next((item for item in evidence if item["path"] == ref["path"]), None)
            if old is None:
                evidence.append(ref)
            elif old["sha256"] != ref["sha256"]:
                candidate["all_row_outcome_guard_20260924"].setdefault(
                    "superseded_hashes", {}
                )[ref["path"]] = old["sha256"]
                old["sha256"] = ref["sha256"]
    if found != DUE:
        raise ValueError("Missing due candidate")
    work["updated_at"] = now
    work["last_event_tick"] = now
    temp = WORK.with_suffix(".all_row_guard.tmp")
    with temp.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temp.replace(WORK)


if __name__ == "__main__":
    main()
