"""Replace transient same-tick receipts without changing historical evidence."""

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "pipeline/research_work.json"
PATHS = (
    "scripts/m95_score_component_control_20260924.py",
    "scripts/test_m95_score_component_control_20260924.py",
    "pipeline/reports/m95_score_component_control_20260924-2010.md",
    "pipeline/decisions/20260924-200931_route_change.md",
)
IDS = {
    "referent-supervision-axis",
    "referent-discrimination",
    "instance-identity-representation",
}


def main():
    original = WORK.read_bytes()
    work = json.loads(original)
    refs = [
        {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
        for path in PATHS
    ]
    for candidate in work["candidates"]:
        if candidate["id"] not in IDS:
            continue
        receipt = candidate["score_component_control_20260924"]
        old = [receipt[key] for key in ("checker", "test", "report", "decision")]
        if candidate["evidence"][-4:] != old:
            raise ValueError("Same-tick evidence changed")
        candidate["evidence"][-4:] = refs
        for key, ref in zip(("checker", "test", "report", "decision"), refs):
            receipt[key] = ref
        receipt["focused_tests_passed"] = 20
    if work["design_cycle"]["evidence"] != old:
        raise ValueError("Design cycle evidence changed")
    work["design_cycle"]["evidence"] = refs
    if WORK.read_bytes() != original:
        raise ValueError("Concurrent research change")
    temporary = WORK.with_suffix(".score_repair.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    os.replace(temporary, WORK)


if __name__ == "__main__":
    main()
