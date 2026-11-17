"""Attach bounded nearest-collision evidence to the three due diagnoses."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATHS = (
    "pipeline/reports/m95_nearest_collision_readiness_20260924-1111.md",
    "scripts/m95_exclusion_cause_audit_20260924.py",
    "scripts/test_m95_exclusion_cause_audit_20260924.py",
)
IDS = {
    "referent-supervision-axis",
    "referent-discrimination",
    "instance-identity-representation",
}


def reference(path):
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
    work_path = ROOT / "pipeline/research_work.json"
    work = json.loads(work_path.read_text(encoding="utf-8"))
    refs = [reference(path) for path in PATHS]
    now = datetime.now().astimezone().isoformat()
    selected = [item for item in work["candidates"] if item["id"] in IDS]
    if len(selected) != len(IDS) or any(item["stage"] != "diagnosis" for item in selected):
        raise ValueError("Diagnosis stage differs")
    for item in selected:
        known = {entry["path"]: entry for entry in item["evidence"]}
        if PATHS[0] in known:
            raise ValueError("Progress already persisted")
        for ref in refs:
            if ref["path"] in known:
                known[ref["path"]]["sha256"] = ref["sha256"]
            else:
                item["evidence"].append(ref)
        item["nearest_collision_readiness_20260924"] = {
            "timestamp": now,
            "report": refs[0],
            "checker": refs[1],
            "test": refs[2],
            "focused_tests_passed": 24,
            "native_execution_completed": False,
            "admission": False,
        }
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = (
        "When authorized GPU7 clears, capture 256 ordered TRAIN matcher rows; "
        "report nearest-query collisions separately from GT-mask misbinding "
        "before six-row and four-scene attribution."
    )
    temporary = work_path.with_suffix(".nearest-collision.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(work_path)
    print(json.dumps({"updated": sorted(IDS), "report": refs[0]}))


if __name__ == "__main__":
    main()
