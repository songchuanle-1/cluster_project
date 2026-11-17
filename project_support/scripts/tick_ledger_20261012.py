"""Structured candidate changes guarded by the actual foreground lease."""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("create", "update", "cycle"))
    parser.add_argument("--token", required=True)
    parser.add_argument("--id")
    parser.add_argument("--record", type=Path, required=True)
    args = parser.parse_args()
    owner = load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    if (owner["token"] != args.token
            or owner["thread_id"] != os.environ["CODEX_THREAD_ID"]):
        raise RuntimeError("Actual owning foreground lease required")
    record = load(args.record)

    def bind(value):
        if isinstance(value, dict):
            for ref in value.get("evidence", []):
                path = (ROOT / ref["path"]).resolve()
                if not path.is_relative_to(ROOT):
                    raise ValueError("Evidence must stay in this project")
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                if ref.get("sha256") and ref["sha256"] != actual:
                    raise ValueError("Existing evidence hash mismatch")
                ref["sha256"] = actual
            for child in value.values():
                bind(child)
        elif isinstance(value, list):
            for child in value:
                bind(child)
    bind(record)
    path = ROOT / "pipeline/research_work.json"
    work = load(path)
    if args.action == "cycle":
        work["design_cycle"] = record
    else:
        if not args.id:
            raise ValueError("Stable ID required")
        rows = [r for r in work["candidates"] if r["id"] == args.id]
        if args.action == "create":
            if rows:
                raise ValueError("ID exists; update it instead")
            record["id"] = args.id
            work["candidates"].append(record)
        else:
            if len(rows) != 1:
                raise ValueError("Unique existing candidate required")
            refs = rows[0].setdefault("evidence", [])
            refs.extend(r for r in record.pop("evidence", []) if r not in refs)
            rows[0].update(record)
        work.pop("design_cycle", None)
    path.write_text(json.dumps(work, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8")
    print(json.dumps({"action": args.action, "id": args.id,
                      "stage": record.get("stage"), "token": args.token}))


if __name__ == "__main__":
    main()
