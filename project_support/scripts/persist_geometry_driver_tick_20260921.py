"""Persist the bounded event tick; synthetic tests never advance native gates."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


PRIOR = "pipeline/reports/relocated_replay_progress_20260921-0415.json"
REPORT = "pipeline/reports/relocated_driver_progress_20260921-0515.json"
RETRY = "2026-09-21T06:07:00+08:00"
NEXT = (
    "Continue the existing diagnostic, not a new mechanism. Internal run_relocated "
    "now joins saved receipt preparation, server-4 capacity predicate, replay_forward "
    "and evaluate; native execution validator/model callbacks and host provisioning "
    "remain unimplemented/unverified. Next audit the separate driver against actual "
    "model constructor/checkpoint/data dependencies and design the production "
    "execution validator contract with fail-closed host/allocation/source checks; "
    "reuse existing runtime and dependency inventory, no duplicate wrapper/review. "
    "Retry server-4 once at/after " + RETRY + ". On verified SSH check runtime/code/"
    "data/work paths, GPU0/1 occupancy and slot coordination; verify dependencies/"
    "extension ABI/assets,3 saved artifacts/6 data hashes and Linux isolation. "
    "Then collate3040/3893 and run exact saved replay; export3921/4278 retaining31. "
    "Never regenerate recovered groups or execute legacy server-6/GPU7 CLI.")
BLOCKER = (
    "One scheduled server-4 SSH attempt refused port22. Native runtime/GPU/data/"
    "checkpoint bytes and Linux enforcement unverified. Separate driver tests are "
    "synthetic; trusted execution/source/model callbacks are not a production "
    "authorization boundary. No native geometry capture or checkpoint recovery.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T21:07:07.619746+00:00"):
        raise ValueError("Wrong tick")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Current decision required")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_relocated_geometry_driver_20260921"] + read(PRIOR)["validation"]["modules"]
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not tests.wasSuccessful():
        raise ValueError("Bounded regression failed")
    migration = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for row in read(migration)["evidence"]:
        if file_sha256(ROOT / row["path"]) != row["sha256"]:
            raise ValueError("Original migration evidence drift")
    paths = [
        PRIOR, migration, args.decision, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/relocated_geometry_driver_20260921.py",
        "scripts/test_relocated_geometry_driver_20260921.py",
        "scripts/persist_geometry_driver_tick_20260921.py",
        "scripts/relocated_saved_replay_20260921.py",
        "scripts/saved_geometry_replay_20260920.py",
        "scripts/saved_physical_location_20260920.py",
        "scripts/referent_geometry_registry_20260919.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=1,
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            command='ssh -o BatchMode=yes -o ConnectTimeout=8 -o ConnectionAttempts=1 '
                    'songcl@192.168.1.137 "hostname"',
            evidence_basis="Observed exec_command this tick; no scripted retry",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(
            tests_run=tests.testsRun, tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            modules=modules, new_tests=19, output=stream.getvalue(),
            native_data_loaded=False, bubblewrap_execution=False),
        completed_work=[
            "Separate internal driver joins original saved replay preparation to capture/evaluation.",
            "Exact3040/3893, full31 joins, original producer and receipt hashes preserved.",
            "Reuses server-4 GPU0/1 fresh idle capacity predicate before model allocation.",
            "External execution check required before loading and again before allocation.",
            "Rechecks source, original location, prepared inputs and receipt bytes after forward.",
            "Failure records and atomic final success publication; no resampling, CLI or dispatch.",
            "Eighteen synthetic full31 orchestration tests plus real replay/evaluator integration "
            "on a separate two-row synthetic fixture; native model/runtime still mocked."],
        registry_denominator=31, physical_bindings_verified=9, physical_bindings_missing=22,
        model_geometry_captures=0, internal_driver_integration=True,
        production_execution_validator_implemented=False, native_cli_implemented=False,
        destination_bytes_verified=False, native_cpu_execution=False,
        native_gpu_execution=False, checkpoint_transfer=False, training_tree_sync=False,
        training_launch=False, admission=False, scientific_validation_complete=False,
        queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Full31 orchestration uses mocked capture/evaluator/native host checks.",
            "Real replay/evaluator integration uses two-row synthetic fixture, not native data.",
            "Execution/source/model callbacks are trusted and not host attestation.",
            "Capacity check is not a reservation; caller owns slot/model teardown.",
            "No native backward/resource/efficacy evidence or M197 checkpoint recovery."])
    work = read("pipeline/research_work.json")
    due = set(context["research_work"]["due_ids"])
    if due != {c["id"] for c in work["candidates"] if c["id"] in due}:
        raise ValueError("Missing due record")
    write_new(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    for candidate in work["candidates"]:
        if candidate["id"] not in due:
            continue
        merged = {e["path"]: e for e in candidate["evidence"]}
        merged.update({e["path"]: e for e in evidence + [entry]})
        candidate.update(
            evidence=list(merged.values()), retry_after=RETRY, blocker=BLOCKER,
            unblock_condition="Verified server-4 runtime/GPU allocation, dependencies/assets/"
                "destination bytes/Linux isolation plus real execution validator; "
                "M197 independently requires compatible checkpoint and safe resume admission.")
        candidate["relocated_driver_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(tests.skipped),
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; internal saved capture integration and19 "
                "synthetic tests plus bounded regression. No native or unauthorized execution.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/GPU0/1 "
                "before read-only M197 last.pth retrieval; validate optimizer/epoch/path "
                "compatibility before safe resume admission. Preserve stopped_unknown; "
                "no server-6 restart. Shared driver does not recover the checkpoint.")
            candidate["latest_progress"] = now + ": SSH refused; checkpoint recovery blocked."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = now + ": Internal driver tested; physical9/model0 unchanged."
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(due), evidence=[entry],
        next_action=NEXT, result="Saved driver integrated/tested; native access blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.relocated_driver_0515.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
