"""Repair same-path hashes after extending the score-component control."""

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "pipeline/research_work.json"
PATHS = (
    "scripts/m95_score_component_control_20260924.py",
    "scripts/test_m95_score_component_control_20260924.py",
    "pipeline/reports/m95_indicator_component_control_20260924-2111.md",
    "pipeline/decisions/20260924-211303_route_change.md",
)
DUE = {
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
    original = WORK.read_bytes()
    work = json.loads(original)
    refs = [reference(path) for path in PATHS]
    by_path = {ref["path"]: ref for ref in refs}
    found = set()

    for candidate in work["candidates"]:
        if candidate["id"] not in DUE:
            continue
        found.add(candidate["id"])
        repaired = []
        seen = set()
        for item in candidate["evidence"]:
            if item["path"] in by_path:
                item["sha256"] = by_path[item["path"]]["sha256"]
            key = (item["path"], item["sha256"])
            if key not in seen:
                repaired.append(item)
                seen.add(key)
        candidate["evidence"] = repaired

    if found != DUE:
        raise ValueError("Missing due IDs")
    work["design_cycle"]["evidence"] = refs
    work["updated_at"] = work["design_cycle"]["timestamp"]

    if WORK.read_bytes() != original:
        raise ValueError("Concurrent research change")
    temporary = WORK.with_suffix(".indicator_repair.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    os.replace(temporary, WORK)


if __name__ == "__main__":
    main()
