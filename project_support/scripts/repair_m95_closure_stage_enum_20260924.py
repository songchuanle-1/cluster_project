"""Move terminal diagnostic records onto the closure-supported stage enum."""

import json
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "pipeline/research_work.json"


def main():
    original = WORK.read_bytes()
    work = json.loads(original)
    repaired = []
    for candidate in work["candidates"]:
        if candidate.get("stage") != "complete":
            continue
        candidate["stage"] = "rejected"
        candidate["closure_repair_20260924"] = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "previous_stage": "complete",
            "new_stage": "rejected",
            "meaning_preserved": (
                "The bounded diagnostic is closed with no admitted mechanism; "
                "its completed evidence remains unchanged."
            ),
            "scientific_effect": "none",
        }
        repaired.append(candidate["id"])

    if not repaired:
        raise ValueError("No complete-stage records found")
    work["updated_at"] = datetime.now().astimezone().isoformat()
    if WORK.read_bytes() != original:
        raise ValueError("Concurrent research change")
    temporary = WORK.with_suffix(".stage_enum_repair.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    os.replace(temporary, WORK)
    print(json.dumps({"repaired": repaired}))


if __name__ == "__main__":
    main()
