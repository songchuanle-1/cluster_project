"""Scoped ledger updates for the current foreground tick."""
import argparse
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
TOKEN = "b395a8b5064a4b6a810cc2285c82c890"
sys.path.insert(0, str(SKILL))
import foreground_tick


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("create", "update", "cycle"))
    parser.add_argument("--id")
    parser.add_argument("--record", type=Path, required=True)
    args = parser.parse_args()
    owner = foreground_tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    if owner["token"] != TOKEN or owner["thread_id"] != os.environ["CODEX_THREAD_ID"]:
        raise RuntimeError("Current owned lease required")
    record = json.loads(args.record.read_text(encoding="utf-8"))
    def bind_evidence(value):
        if isinstance(value, dict):
            for item in value.get("evidence", []):
                path = (ROOT / item["path"]).resolve()
                if not path.is_relative_to(ROOT):
                    raise ValueError("Project evidence only")
                item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            for item in value.values():
                bind_evidence(item)
        elif isinstance(value, list):
            for item in value:
                bind_evidence(item)
    bind_evidence(record)
    work = foreground_tick.load(ROOT / "pipeline/research_work.json")
    if args.action == "cycle":
        record["retry_after"] = (datetime.now().astimezone() + timedelta(hours=1)).isoformat()
        work["design_cycle"] = record
        foreground_tick.save(ROOT / "pipeline/research_work.json", work)
        print(json.dumps({"action": "cycle", "stop_reason": record["stop_reason"],
                          "retry_after": record["retry_after"], "token": TOKEN}))
        return
    if not args.id:
        raise ValueError("Stable candidate ID required")
    matches = [row for row in work["candidates"] if row["id"] == args.id]
    if args.action == "create":
        if matches:
            raise ValueError("Stable ID already exists; use update")
        record["id"] = args.id
        work["candidates"].append(record)
    else:
        if len(matches) != 1:
            raise ValueError("Exactly one stable candidate required")
        row = matches[0]
        evidence = row.setdefault("evidence", [])
        evidence.extend(item for item in record.pop("evidence", []) if item not in evidence)
        row.update(record)
    work.pop("design_cycle", None)
    foreground_tick.save(ROOT / "pipeline/research_work.json", work)
    print(json.dumps({"id": args.id, "action": args.action,
                      "stage": record.get("stage"), "token": TOKEN}))


if __name__ == "__main__":
    main()
