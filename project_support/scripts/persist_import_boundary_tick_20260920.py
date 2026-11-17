"""Persist this bounded import-boundary implementation tick, without admission."""
import argparse
from datetime import datetime
import io
import json
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from saved_replay_migration_20260920 import ROOT

PRIOR = "pipeline/reports/native_batch_validation_progress_20260920-1418.json"
REPORT = "pipeline/reports/pinned_import_progress_20260920-1515.json"
RETRY = "2026-09-20T16:07:00+08:00"
NEXT = (
    "Retry server-4 SSH once at/after " + RETRY + ". Verify runtime, code/data and "
    "GPU0/1 occupancy before transfer or native work. Continue the same CPU "
    "entrypoint: integrate tested PinnedDiagnosticImports before producer imports "
    "in a fresh child process; implement server identity/runtime checks and "
    "scratch-only write enforcement with mocked CLI tests. Reuse native_callbacks, "
    "NativeBatchValidator and run_collation. Then add location-aware prepare_replay. "
    "After destination verification retrieve exact3040/3893 read-only, verify3 "
    "artifacts/6 data hashes and collate; then export3921/4278 with full31 rows. "
    "Never regenerate saved groups; GPU forwards require actual coordinated capacity.")
BLOCKER = (
    "One server-4 SSH attempt refused port22. Destination runtime/data/GPU and "
    "checkpoint bytes remain unverified; new native source/local work prohibited. "
    "Byte-pinned imports now have synthetic tests but are not integrated in a "
    "native CLI. Host/runtime checks, scratch-only writes and relocated replay "
    "remain executable local implementation work.")


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_new(path, value):
    with (ROOT / path).open("x", encoding="ascii") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T07:07:08.074058+00:00"):
        raise ValueError("Wrong tick")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Current decision required")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_pinned_diagnostic_imports_20260920"] + read(PRIOR)["validation"]["modules"]
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not tests.wasSuccessful():
        raise ValueError("Regression failed")
    contract = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for row in read(contract)["evidence"]:
        if file_sha256(ROOT / row["path"]) != row["sha256"]:
            raise ValueError("Migration evidence changed")
    paths = [PRIOR, contract, args.decision, "pipeline/goal.json", "SERVERS.yaml",
             "scripts/pinned_diagnostic_imports_20260920.py",
             "scripts/test_pinned_diagnostic_imports_20260920.py",
             "scripts/persist_import_boundary_tick_20260920.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(server="server-4", attempts=1, returncode=1,
            command="ssh -o BatchMode=yes -o ConnectTimeout=10 -o ConnectionAttempts=1 songcl@192.168.1.137 hostname",
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(tests_run=tests.testsRun,
            tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            new_tests=21, modules=modules, output=stream.getvalue(),
            local_native_data_loaded=False),
        completed_work=[
            "Manifest digest and every declared file verified; paths and symlinks rejected.",
            "Producer and dependencies compiled from checked bytes; cached pyc ignored.",
            "Pre-imported producers rejected even with matching path or module alias.",
            "Imported identity and sources rechecked; owned modules/finder cleaned on failure.",
            "Synthetic shadow-path, stale-pyc, drift, dependency and failure tests.",
            "Immutable migration evidence rehashed; training tree untouched."],
        registry_denominator=31, physical_bindings_verified=9, physical_bindings_missing=22,
        model_geometry_captures=0, native_collation_completed=False,
        native_cli_completed=False, scratch_write_enforcement_completed=False,
        relocated_replay_completed=False, destination_bytes_verified=False,
        native_cpu_execution=False, native_gpu_execution=False,
        checkpoint_transfer=False, training_tree_sync=False, training_launch=False,
        admission=False, scientific_validation_complete=False,
        queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        open_questions=["server-4 restoration and destination compatibility",
                        "M197 checkpoint/optimizer/epoch recovery compatibility"],
        limitations=[
            "Import boundary is not a security sandbox or native host authorization.",
            "External dependencies and native extensions retain ordinary import behavior.",
            "Fresh-process integration and scratch-write enforcement remain incomplete.",
            "Real symlink creation may be skipped on Windows; mock guard tested.",
            "No native data, forward/backward, efficiency, efficacy or novelty evidence.",
            "Shared import implementation does not advance M197 checkpoint recovery."])
    write_new(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    work = read("pipeline/research_work.json")
    found = set()
    for candidate in work["candidates"]:
        if candidate["id"] not in context["research_work"]["due_ids"]:
            continue
        found.add(candidate["id"])
        merged = {e["path"]: e for e in candidate["evidence"]}
        merged.update({e["path"]: e for e in evidence + [entry]})
        candidate["evidence"] = list(merged.values())
        candidate["retry_after"] = RETRY
        candidate["blocker"] = BLOCKER
        candidate["unblock_condition"] = (
            "Verified server-4 runtime/data/source and destination bytes; tested "
            "CPU CLI with pinned imports and scratch-only writes; relocated replay. "
            "GPU needs coordinated capacity; M197 separately needs checkpoint/admission.")
        candidate["pinned_import_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(tests.skipped),
            physical_bindings_verified=9, model_geometry_captures=0,
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; synthetic byte-pinned import "
                "implementation/tests; no unauthorized native work.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify destination runtime/"
                "data/GPU0/1 before read-only retrieval of M197 last.pth; validate checkpoint "
                "optimizer/epoch/path compatibility before safe resume admission. "
                "No restart on server-6; preserve stopped_unknown. Shared import tests "
                "do not establish checkpoint recovery, efficacy or novelty.")
            candidate["latest_progress"] = now + ": SSH refused; no checkpoint recovery."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = now + ": Byte-pinned import tests; physical9/model0 unchanged."
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Missing due record")
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(found), evidence=[entry],
        next_action=NEXT, result="Import-boundary subcomponent tested; native access blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.import_boundary_1515.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=REPORT, tests=tests.testsRun,
                          passed=report["validation"]["tests_passed"],
                          skipped=len(tests.skipped))))


if __name__ == "__main__":
    main()
