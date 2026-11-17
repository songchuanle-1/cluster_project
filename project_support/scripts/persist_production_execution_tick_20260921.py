"""Persist production execution guard/driver evidence without native promotion."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


REPORT = "pipeline/reports/production_execution_progress_20260921-1415.json"
PRIOR = "pipeline/reports/pinned_launcher_progress_20260921-1315.json"
RETRY = "2026-09-21T15:07:00+08:00"
BLOCKER = (
    "Monitor preflight reported server-4 unreachable at 14:07. No remote "
    "command ran; runtime, GPU occupancy, installed dependency bytes/ABI, "
    "assets and Linux isolation remain unverified. Synthetic execution-guard "
    "tests are not native validation.")
NEXT = (
    "Continue the existing diagnostic, no new review or variant. The synthetic "
    "production driver/external execution guard is implemented. On the next "
    "tick, retry server-4 once at/after " + RETRY + "; while unreachable, "
    "perform a bounded static audit of installed dependency/bootstrap roots and "
    "extension shared-library provenance without asserting ABI. With verified "
    "host, held GPU0/1 slot, dependency/assets/isolation receipts and 3 "
    "artifacts/6 data hashes, collate saved3040/3893 and exact replay, then "
    "export 3921/4278 retaining31. Never regenerate recovered groups or run "
    "legacy server-6/GPU7 CLI.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-21T06:07:07.067217+00:00"):
        raise ValueError("Wrong event snapshot")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Missing decision")
    if (ROOT / REPORT).exists():
        raise ValueError("Report already exists")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    prior = read(PRIOR)
    modules = [
        "test_server4_execution_validator_20260921",
    ] + prior["validation"]["modules"]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Regression failed")
    paths = [
        PRIOR, args.decision, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/server4_execution_validator_20260921.py",
        "scripts/production_saved_collation_driver_20260921.py",
        "scripts/test_server4_execution_validator_20260921.py",
        "scripts/pinned_bootstrap_launcher_20260921.py",
        "scripts/preidentity_handoff_20260921.py",
        "scripts/pinned_diagnostic_imports_20260920.py",
        "scripts/persist_production_execution_tick_20260921.py",
    ]
    evidence = [dict(path=path, sha256=file_sha256(ROOT / path)) for path in paths]
    now = datetime.now().astimezone().isoformat()
    monitor = context["preflight"]["monitor_output"]
    if "server-4 (192.168.1.137)" not in monitor or "[不可达]" not in monitor:
        raise ValueError("Preflight did not report server-4 unreachable")
    report = dict(
        schema_version=1,
        generated_at=now,
        snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"],
        evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, source="monitor_preflight",
            command_not_run=True, unreachable=True,
            evidence_basis=(
                "The already-completed 14:07 preflight reported server-4 "
                "[unreachable]; no duplicate monitor or SSH call was made."),
            runtime_verified=False, gpu_occupancy_verified=False),
        completed_work=[
            "Added a host-side ProductionExecutionGuard that requires an external callable slot lease.",
            "The guard refreshes host and GPU capacity observations and hashes dependency, asset and isolation evidence.",
            "It freezes the exact receipt, runtime, capacity and slot proof into one write-once driver context.",
            "The child production driver revalidates the context and supplies exact held-slot and execution checks to PreIdentityHandoff.collect.",
            "The child rechecks parent ownership, runtime identity, CUDA visibility and evidence bytes throughout collection.",
            "Stale receipts, slot loss, UUID/runtime drift, capacity failure and evidence drift block before/inside launch.",
            "The production driver rejects any positive execution, scientific or admission claims.",
            "Ten focused synthetic guard/driver tests and the bounded regression passed.",
            "No actual lease, dependency/ABI, asset, isolation, GPU, model or native execution was claimed."],
        validation=dict(
            tests_run=result.testsRun,
            tests_passed=result.testsRun - len(result.skipped),
            new_tests=10,
            modules=modules,
            skipped=[dict(test=str(test), reason=reason)
                     for test, reason in result.skipped],
            output=stream.getvalue(),
            native_data_loaded=False),
        physical_bindings_verified=9,
        physical_bindings_missing=22,
        registry_denominator=31,
        model_geometry_captures=0,
        native_execution_completed=False,
        scientific_validation_complete=False,
        native_backward_verified=False,
        resources_verified=False,
        admission=False,
        training_launch=False,
        checkpoint_transfer=False,
        queue_changed=False,
        queue_sha256=queue_hash,
        blocker=BLOCKER,
        next_action=NEXT,
        retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "The external callbacks supplied in tests are synthetic; no real lease, dependency, asset or isolation verifier was exercised.",
            "The driver was tested directly with a fake boundary, not with real PreIdentityHandoff under the isolated launcher.",
            "The pinned launcher still proves source identity/startup, not sandbox enforcement or fd-based exec.",
            "Installed extension shared-library provenance and ABI remain unverified.",
            "No actual GPU identity, native forward/backward, model, resources, efficacy or admission evidence.",
            "Shared M95 implementation does not recover M197."])
    work = read("pipeline/research_work.json")
    due = set(context["research_work"]["due_ids"])
    if due != {candidate["id"] for candidate in work["candidates"]
               if candidate["id"] in due}:
        raise ValueError("Missing due candidates")
    write_new(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    for candidate in work["candidates"]:
        if candidate["id"] not in due:
            continue
        merged = {item["path"]: item for item in candidate["evidence"]}
        merged.update({item["path"]: item for item in evidence + [entry]})
        candidate.update(
            evidence=list(merged.values()),
            blocker=BLOCKER,
            retry_after=RETRY,
            next_action=NEXT,
            unblock_condition=(
                "Verified authorized server-4 runtime, held GPU0/1 slot, real "
                "dependency/shared-library and asset evidence, verified Linux "
                "isolation and production driver/guard integration. M197 "
                "separately requires checkpoint/optimizer/epoch/path and resume "
                "admission."),
            latest_progress=(
                now + ": production execution guard/driver implemented and tested synthetically."))
        candidate["production_execution_progress"] = dict(
            timestamp=now,
            report=REPORT,
            report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"],
            tests_skipped=len(result.skipped),
            native_execution_completed=False,
            scientific_validation_complete=False,
            alternatives_attempted=(
                "Server-4 remained unreachable in preflight; ten new synthetic "
                "guard/driver tests plus bounded regression. No native packages, "
                "lease, data or hosts were used."))
        if candidate["id"] == "referent-supervision-axis":
            candidate["latest_progress"] = (
                now + ": server-4 unreachable; production guard/driver added "
                "separately for saved diagnostics.")
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/"
                "GPU0/1 before read-only M197 checkpoint recovery; validate "
                "optimizer/epoch/paths and safe resume admission. Preserve "
                "stopped_unknown; no server-6 restart. Shared M95 loader does "
                "not recover M197.")
    work["last_event_tick"] = dict(
        timestamp=now,
        mode="event",
        due_ids=sorted(due),
        evidence=[entry],
        next_action=NEXT,
        result=(
            "Production execution guard/driver implemented and tested "
            "synthetically; server-4 remains unverified and no queue changed."))
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.production_execution_1415.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
