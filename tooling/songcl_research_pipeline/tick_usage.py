"""Best-effort local per-response usage, without exporting conversation text."""
import json
import os
from pathlib import Path
import sqlite3
from contextlib import closing


FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens",
          "reasoning_output_tokens", "total_tokens")
BOUNDARY = ("Local response records appended after begin and visible before receipt; "
            "excludes earlier reads, late usage, and final answer. Not a billing total.")


def cursor(thread_id):
    try:
        home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
        with closing(sqlite3.connect((home / "state_5.sqlite").as_uri() + "?mode=ro", uri=True,
                                     timeout=1)) as connection:
            row = connection.execute(
                "SELECT rollout_path FROM threads WHERE id=?", (thread_id,)).fetchone()
        path = Path(row[0])
        size = path.stat().st_size
        # Guard against log replacement and a partial last line.
        with path.open("rb") as stream:
            if size:
                stream.seek(size - 1)
                partial = stream.read(1) != b"\n"
            else:
                partial = False
        return {"path": str(path), "offset": size, "partial": partial,
                "inode": path.stat().st_ino, "thread_id": thread_id}
    except (OSError, sqlite3.Error, TypeError, ValueError):
        return None


def collect(start):
    unavailable = {"status": "unavailable", "calls": None, "boundary": BOUNDARY}
    if not start:
        return unavailable
    try:
        path = Path(start["path"])
        if path.stat().st_size < start["offset"] or path.stat().st_ino != start["inode"]:
            return {**unavailable, "reason": "log_replaced_or_truncated"}
        records = {}
        malformed = 0
        with path.open("rb") as stream:
            stream.seek(start["offset"])
            if start.get("partial"):
                stream.readline()
            for line in stream:
                if b'"token_usage_record"' not in line:
                    continue
                try:
                    event = json.loads(line)
                    payload = event.get("payload", {})
                    if event.get("type") != "token_usage_record":
                        continue
                    if payload.get("thread_id") != start["thread_id"]:
                        continue
                    rid, usage = payload.get("response_id"), payload.get("usage")
                    if rid and isinstance(usage, dict):
                        records[rid] = usage
                except (ValueError, TypeError):
                    malformed += 1
        if not records:
            return {**unavailable, "reason": "no_response_records_visible"}
        totals = {
            key: sum(r[key] for r in records.values())
            if all(isinstance(r.get(key), int) and r[key] >= 0 for r in records.values())
            else None for key in FIELDS
        }
        inp, cached = totals["input_tokens"], totals["cached_input_tokens"]
        totals["uncached_input_tokens"] = inp - cached if (
            inp is not None and cached is not None and cached <= inp) else None
        return {"status": "partial_window", "calls": len(records), **totals,
                "malformed_records": malformed, "boundary": BOUNDARY}
    except (OSError, KeyError, TypeError, ValueError):
        return unavailable


def work_snapshot(pipeline):
    try:
        path = pipeline / "research_work.json"
        work = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        return {c["id"]: {"stage": c.get("stage"), "evidence": c.get("evidence", [])}
                for c in work.get("candidates", [])}
    except (OSError, ValueError, KeyError, TypeError):
        return None


def outcomes(pipeline, before):
    after = work_snapshot(pipeline)
    if before is None or after is None:
        return {"status": "unavailable"}
    changed = {cid: c for cid, c in after.items() if before.get(cid) != c}
    return {
        "status": "observed", "new_candidates": sum(cid not in before for cid in after),
        "changed_candidates": len(changed),
        "new_evidence_references": sum(
            entry not in before.get(cid, {}).get("evidence", [])
            for cid, c in changed.items() for entry in c["evidence"]),
        "advanced_to_training": sum(c["stage"] == "training" and
                                   before.get(cid, {}).get("stage") != "training"
                                   for cid, c in changed.items()),
        "dispositions": {stage: sum(c["stage"] == stage for c in changed.values())
                         for stage in ("admission", "training", "rejected", "blocked", "complete")},
        "meaning": "Artifact/stage changes only, not a claim of scientific benefit.",
    }
