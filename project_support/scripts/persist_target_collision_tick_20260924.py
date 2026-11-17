"""Persist a bounded event continuation for the three stable diagnoses."""
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "pipeline/research_work.json"
DUE = {
    "referent-supervision-axis",
    "referent-discrimination",
    "instance-identity-representation",
}
FILES = [
    "pipeline/reports/m95_target_nearest_collision_readiness_20260924-1209.md",
    "scripts/m95_exclusion_cause_audit_20260924.py",
    "scripts/test_m95_exclusion_cause_audit_20260924.py",
]


def main():
    work = json.loads(WORK.read_text(encoding="utf-8"))
    now = datetime.now(timezone(timedelta(hours=8))).isoformat()
    receipt = {
        "timestamp": now,
        "report": {
            "path": FILES[0],
            "sha256": hashlib.sha256((ROOT / FILES[0]).read_bytes()).hexdigest(),
        },
        "checker": {
            "path": FILES[1],
            "sha256": hashlib.sha256((ROOT / FILES[1]).read_bytes()).hexdigest(),
        },
        "test": {
            "path": FILES[2],
            "sha256": hashlib.sha256((ROOT / FILES[2]).read_bytes()).hexdigest(),
        },
        "tests_passed": 25,
        "native_execution_completed": False,
        "admission": False,
    }
    touched = set()
    for candidate in work["candidates"]:
        if candidate["id"] not in DUE:
            continue
        if candidate.get("stage") != "diagnosis":
            raise ValueError("Unexpected candidate stage")
        candidate["target_nearest_collision_readiness_20260924"] = receipt
        candidate["latest_progress"] = (
            now + ": Target-specific nearest collision control passes 25 "
            "synthetic tests; native incidence unknown. GPU7 external occupancy "
            "prevents safe native capture."
        )
        candidate["blocker"] = "External GPU7 job at 100% instantaneous utilization"
        candidate["unblock_condition"] = (
            "Authorized GPU7 capacity clears and SSH/runtime/data/checkpoint "
            "provenance and actual memory/occupancy are verified."
        )
        touched.add(candidate["id"])
    if touched != DUE:
        raise ValueError("Due candidate set mismatch")
    work["updated_at"] = now
    with WORK.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(work, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print("Updated three diagnosis IDs")


if __name__ == "__main__":
    main()
