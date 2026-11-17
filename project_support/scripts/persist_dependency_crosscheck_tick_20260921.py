"""Persist the POSIX fixture cross-check without promoting target facts."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


REPORT = "pipeline/reports/dependency_crosscheck_progress_20260921-1815.json"
PRIOR = "pipeline/reports/dependency_collector_progress_20260921-1750.json"
RETRY = "2026-09-21T18:45:00+08:00"
BLOCKER = (
    "Server-4 remains unavailable in the 18:07 preflight, and no observation "
    "has been collected. The collector-to-validator POSIX fixture cross-check "
    "is complete, but no target root, bootstrap module, package file, ELF "
    "declaration, shared library or GPU was observed. ABI, loader resolution, "
    "runtime, isolation and native execution remain unverified.")
GENERAL_NEXT = (
    "Continue the existing saved-only diagnostic, no new review or variant. "
    "Retry server-4 once at/after " + RETRY + ". If reachable, materialize an "
    "explicit collection plan, run dependency_observation_collector_20260921 "
    "in the target interpreter, validate the manifest with "
    "dependency_provenance_audit_20260921, and inspect M197 "
    "checkpoint/optimizer/epoch/paths. If unreachable, keep the implementation "
    "blocked; do not duplicate the completed fixture cross-check or create a "
    "renamed review/variant. Do not assert ABI, loader resolution or runtime "
    "equivalence. Only after verified host, held GPU0/1 slot, dependency/asset/"
    "isolation receipts and 3 artifacts/6 data hashes may saved3040/3893 "
    "collation advance; then export3921/4278 retaining31. Never regenerate "
    "recovered groups or run legacy server-6/GPU7 CLI.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-21T10:07:29.392847+00:00"
            or context["research_work"]["due_ids"] != [
                "referent-causality-audit"]):
        raise ValueError("Wrong event snapshot")
    decision = (ROOT / args.decision).resolve()
    if (not decision.is_relative_to(ROOT / "pipeline/decisions")
            or not decision.is_file()):
        raise ValueError("Missing decision")
    if (ROOT / REPORT).exists():
        raise ValueError("Report already exists")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    prior = read(PRIOR)
    modules = list(prior["validation"]["modules"])
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Regression failed")

    paths = [
        PRIOR, args.decision, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/dependency_observation_collector_20260921.py",
        "scripts/test_dependency_observation_collector_20260921.py",
        "scripts/dependency_provenance_audit_20260921.py",
        "scripts/test_dependency_provenance_audit_20260921.py",
        "scripts/saved_dependency_inventory_20260921.py",
        "scripts/persist_dependency_crosscheck_tick_20260921.py",
    ]
    evidence = [
        dict(path=path, sha256=file_sha256(ROOT / path)) for path in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1,
        generated_at=now,
        snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"],
        evidence=evidence,
        connectivity=dict(
            server="server-4",
            attempts=0,
            source="deferred_direct_retry",
            preflight_reachable=False,
            retry_after=RETRY,
            runtime_verified=False,
            gpu_occupancy_verified=False,
            roots_observed=False),
        crosscheck=dict(
            fixture="synthetic-posix-identities-v1",
            test="test_posix_fixture_crosses_collector_and_validator",
            collector_to_validator=True,
            canonical_observation_written=True,
            observation_hash_checked=True,
            receipt_written=True,
            receipt_reloaded=True,
            package_count=9,
            declared_library_count=2,
            target_paths_observed=False,
            target_packages_imported=False,
            native_extension_executed=False,
            abi_compatibility_checked=False,
            runtime_loader_resolution_verified=False,
            native_execution_completed=False,
            scientific_validation_complete=False,
            admission=False),
        completed_work=[
            "Added an end-to-end POSIX fixture test that starts from the collector output contract.",
            "The test writes the canonical observation, hashes it, validates it, writes the receipt, and reloads it.",
            "The fixture covers all nine direct packages, ELF DT_NEEDED declarations and cache candidates.",
            "No synthetic fixture row is recorded as a target-host observation.",
            "No new review, experiment variant, queue mutation, training launch or GPU use occurred."],
        validation=dict(
            tests_run=result.testsRun,
            tests_passed=result.testsRun - len(result.skipped),
            new_tests=1,
            modules=modules,
            skipped=[dict(test=str(test), reason=reason)
                     for test, reason in result.skipped],
            output=stream.getvalue(),
            native_data_loaded=False,
            abi_compatibility_checked=False),
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
        next_action=GENERAL_NEXT,
        retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "The cross-check uses synthetic POSIX path identities backed by temporary local files.",
            "It proves collector/validator schema and hash handoff, not a POSIX host runtime.",
            "No target Python, site-packages, package metadata, extension ELF or system library was read.",
            "The receipt records declarations; it does not prove loaded bytes or linker resolution.",
            "No sandbox, GPU slot, assets, data, backward, resources or admission evidence exists."])

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
            stage="implementation",
            evidence=list(merged.values()),
            blocker=BLOCKER,
            retry_after=RETRY,
            next_action=GENERAL_NEXT,
            unblock_condition=(
                "Verified authorized server-4 runtime; collector output "
                "validated by dependency_provenance_audit_20260921; "
                "independently verified runtime loader/ABI boundary; held "
                "GPU0/1 slot; assets and Linux isolation. M197 separately "
                "requires read-only checkpoint, optimizer, epoch/path and "
                "safe-resume admission."),
            latest_progress=(
                now + ": collector-to-validator POSIX fixture crossed "
                "canonical observation, hash, receipt and reload; server "
                "remains unobserved."))
        candidate["dependency_crosscheck_progress"] = dict(
            timestamp=now,
            report=REPORT,
            report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"],
            tests_skipped=len(result.skipped),
            collector_to_validator=True,
            target_paths_observed=False,
            native_execution_completed=False,
            scientific_validation_complete=False,
            alternatives_attempted=(
                "Deferred the next direct SSH retry to 18:45 and completed "
                "the permitted POSIX fixture cross-check. No target package, "
                "ELF, data, GPU or host was read."))
    work["last_event_tick"] = dict(
        timestamp=now,
        mode="event",
        due_ids=sorted(due),
        evidence=[entry],
        next_action=GENERAL_NEXT,
        result=(
            "Collector-to-validator POSIX fixture cross-check completed; "
            "server-4 remains unverified and no queue changed."))
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.dependency_crosscheck_1815.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
