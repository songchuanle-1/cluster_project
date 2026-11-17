"""Bounded local-only M234 archived-log event index; default is no-op."""
import argparse
import collections
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
TICK = OUT.parent
EXPECTED_TOKEN = "df8e31277a3644ffb73d674a6d58f4c6"
PER_FILE_CAP = 8 * 1024 * 1024
TOTAL_CAP = 16 * 1024 * 1024
EVENT_CAP = 32
PRE = 8
POST = 24
TEXT_CAP = 2048
PATTERNS = {
    "worker_failure": rb"unexpected (?:segmentation fault|bus error).{0,100}worker|dataloader worker|worker\s*\(pid",
    "segmentation_fault": rb"segmentation fault|sigsegv|segfault",
    "bus_error": rb"sigbus|bus error",
    "fatal_python_or_faulthandler": rb"fatal python error|faulthandler|current thread 0x|thread 0x[0-9a-f]+.*most recent call first",
    "allocator_corruption": rb"malloc\(\)|malloc:|free\(\):|double free|corrupted (?:size|double|top)|heap corruption|memory corruption|invalid (?:next size|pointer)|munmap_chunk",
    "native_backtrace_marker": rb"c\+\+ traceback|c stack trace|native (?:stack|backtrace)|backtrace:|stack trace:",
    "abort": rb"\bsigabrt\b|\baborted\b",
}
COMPILED = {key: re.compile(value, re.I) for key, value in PATTERNS.items()}
NL = re.compile(rb"\r\n|\r|\n")


def utcnow():
    return dt.datetime.now(dt.timezone.utc)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def stat_record(path):
    st = path.stat()
    return {"size": st.st_size, "mtime_ns": st.st_mtime_ns,
            "mtime_utc": dt.datetime.fromtimestamp(st.st_mtime, dt.timezone.utc).isoformat()}


def display(line_number, start, end, raw):
    text = raw.decode("utf-8", errors="replace")
    return {"line": line_number, "byte_start": start, "byte_end_exclusive": end,
            "text": text[:TEXT_CAP], "text_truncated": len(text) > TEXT_CAP}


def scan(path, expected_sha, budget):
    before = stat_record(path)
    limit = min(PER_FILE_CAP, budget)
    digest = hashlib.sha256()
    scanned = 0
    pending = b""
    offset = 0
    line_no = 0
    ring = collections.deque(maxlen=PRE)
    events = []
    counts = collections.Counter()
    pending_events = []
    max_line_bytes = 0
    cr = lf = crlf = 0

    def process(raw, start, end):
        nonlocal line_no, max_line_bytes, pending_events
        line_no += 1
        max_line_bytes = max(max_line_bytes, len(raw))
        row = display(line_no, start, end, raw)
        for event, remaining in pending_events:
            event["context_after"].append(row)
        pending_events = [(event, remaining - 1) for event, remaining in pending_events if remaining > 1]
        tags = [key for key, pattern in COMPILED.items() if pattern.search(raw)]
        if tags:
            counts.update(tags)
            counts["matching_lines"] += 1
            if len(events) < EVENT_CAP:
                event = dict(row)
                event.update({"tags": tags, "context_before": list(ring), "context_after": []})
                events.append(event)
                pending_events.append((event, POST))
        ring.append(row)

    with path.open("rb") as stream:
        while scanned < limit:
            block = stream.read(min(65536, limit - scanned))
            if not block:
                break
            scanned += len(block)
            digest.update(block)
            pending += block
            consumed = 0
            for match in NL.finditer(pending):
                if match.group() == b"\r" and match.end() == len(pending):
                    break
                sep = match.group()
                cr += sep == b"\r"
                lf += sep == b"\n"
                crlf += sep == b"\r\n"
                process(pending[consumed:match.start()], offset + consumed, offset + match.end())
                consumed = match.end()
            pending = pending[consumed:]
            offset += consumed
    if pending:
        if pending.endswith(b"\r"):
            cr += 1
            process(pending[:-1], offset, offset + len(pending))
        else:
            process(pending, offset, offset + len(pending))
    after = stat_record(path)
    complete = scanned == before["size"]
    stable = before == after
    scanned_sha = digest.hexdigest()
    verified = complete and stable and scanned_sha == expected_sha
    return {
        "path": str(path), "stat_before": before, "stat_after": after,
        "metadata_stable": stable, "bytes_scanned": scanned,
        "scan_byte_range": [0, scanned], "per_file_cap_bytes": PER_FILE_CAP,
        "complete_file_coverage": complete, "byte_scan_truncated": not complete,
        "scanned_bytes_sha256": scanned_sha, "archive_receipt_sha256": expected_sha,
        "full_file_sha256_matches_archive": verified, "line_count": line_no,
        "newline_counts": {"CR": cr, "LF": lf, "CRLF": crlf},
        "max_line_bytes": max_line_bytes, "event_counts": dict(counts),
        "events_stored": len(events), "event_records_truncated": counts["matching_lines"] > EVENT_CAP,
        "events": events, "final_context": list(ring),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-local", action="store_true")
    args = parser.parse_args()
    if not args.execute_local:
        print(json.dumps({"mode": "NOOP", "writes": False, "archive_reads": False}))
        return
    if not sys.dont_write_bytecode:
        raise RuntimeError("Use python -B")
    owner = read_json(TICK / "current_owner_binding.json")
    if owner["token"] != EXPECTED_TOKEN:
        raise RuntimeError("Owner mismatch")
    started = utcnow()
    if not (dt.datetime.fromisoformat(owner["generated_at"]) <= started <
            dt.datetime.fromisoformat(owner["deadline_at"])):
        raise RuntimeError("Outside current lease")
    result_path = OUT / "scan.actual.json"
    if result_path.exists():
        raise RuntimeError("Refusing replay/overwrite")
    archive_path = ROOT / "pipeline/diagnostic_bundles/tick_342a6a92/archive_execution_v2/archive_actual.json"
    archive = read_json(archive_path)
    reconcile_path = ROOT / "pipeline/diagnostic_bundles/tick_342a6a92/reconcile.actual.json"
    reconcile = read_json(reconcile_path)
    if archive["experiment"]["id"] != "M234-RVE" or archive["state"] != "crashed":
        raise RuntimeError("Archive identity mismatch")
    results = []
    remaining = TOTAL_CAP
    archive_root = (ROOT / "Checkpoints/server_4/M234-RVE_terminal_342a6a92_v2").resolve()
    for call in archive["scp_calls"]:
        if call["label"] not in {"registered_stdout", "actual_native_logger"}:
            raise RuntimeError("Unexpected archive")
        path = Path(call["local"]).resolve()
        if not path.is_relative_to(archive_root):
            raise RuntimeError("Archive path outside exact local archive")
        item = scan(path, call["sha256"], remaining)
        item["label"] = call["label"]
        results.append(item)
        remaining -= item["bytes_scanned"]
    if {item["label"] for item in results} != {"registered_stdout", "actual_native_logger"}:
        raise RuntimeError("Missing required archived log")
    passed = all(item["full_file_sha256_matches_archive"] for item in results)
    actual = {
        "owner": owner, "started_at": started.isoformat(), "finished_at": utcnow().isoformat(),
        "kind": "LOCAL_ARCHIVED_WHOLE_BYTE_FATAL_EVENT_INDEX",
        "candidate_id": "fine-leaf-receiver-conditioned-vector-exchange", "experiment": "M234-RVE",
        "read_only_archives": True, "source_path": str(Path(__file__).resolve()),
        "source_sha256": sha(Path(__file__).resolve()),
        "command": "python -B -X utf8 " + str(Path(__file__).resolve()) + " --execute-local",
        "new_tick_owner_applies_only_to_this_local_analysis": True,
        "historical_provenance": {
            "archive_owner_preserved": archive["owner"],
            "archive_receipt_path": str(archive_path), "archive_receipt_sha256": sha(archive_path),
            "terminal_reconcile_path": str(reconcile_path), "terminal_reconcile_sha256": sha(reconcile_path),
            "source_commit": archive["experiment"]["code_commit"],
            "runtime_root": reconcile["observation"]["runtime_root"] if "observation" in reconcile else None,
            "original_training_pid": 3813109, "failed_worker_pid": 3815203,
            "source_runtime_UUID_not_rebound": True,
        },
        "deduplication_check": {
            "scope": ["tick_342a6a92", "tick_14977661", "tick_eb845403", "tick_d2045281"],
            "method": "Targeted rg over JSON/Markdown/Python for full-byte/whole-artifact/event-index and archive filenames; inspected archive receipt and prior diagnoses.",
            "prior_full_byte_fatal_event_index_found": False,
            "prior_archive_decode_scope_bytes_each": 131072,
            "no_claim_of_exhaustive_unrelated_history_review": True,
        },
        "limits": {"per_file_bytes": PER_FILE_CAP, "total_bytes": TOTAL_CAP,
                   "events_per_file": EVENT_CAP, "context_before_lines": PRE,
                   "context_after_lines": POST, "display_characters_per_line": TEXT_CAP},
        "patterns": {key: value.decode("ascii") for key, value in PATTERNS.items()},
        "files": results, "total_bytes_scanned": TOTAL_CAP - remaining,
        "passed": passed, "root_cause": "UNKNOWN",
        "historical_crash_reproduced": False, "training_repair_verified": False,
        "native_gate_or_GPU_compute": False,
        "claim_scope": "Only complete byte coverage for the declared patterns in these two stable archived files. Absence is not proof that no unlogged worker/native fault occurred.",
    }
    with result_path.open("x", encoding="utf-8", newline="\n") as target:
        json.dump(actual, target, indent=2, ensure_ascii=False)
        target.write("\n")
    print(json.dumps({"passed": passed, "actual_path": str(result_path),
                      "actual_sha256": sha(result_path),
                      "total_bytes_scanned": actual["total_bytes_scanned"],
                      "files": [{"label": item["label"], "complete": item["complete_file_coverage"],
                                 "events": item["event_counts"], "stable": item["metadata_stable"]}
                                for item in results]}))


if __name__ == "__main__":
    main()
