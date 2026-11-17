"""Persist the target-runtime dependency plan materializer tick."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


SNAPSHOT = "2026-09-21T11:07:11.858822+00:00"
REPORT = "pipeline/reports/dependency_plan_progress_20260921-1915.json"
PRIOR = "pipeline/reports/dependency_crosscheck_progress_20260921-1815.json"
SEED = "pipeline/diagnostic_bundles/dependency_collection_seed_server4_20260921.json"
RETRY = "2026-09-21T20:15:00+08:00"
EXECUTABLE_DUE = "referent-causality-audit"
BLOCKER = (
    "Direct server-4 SSH retry refused port 22. The target-runtime plan "
    "materializer is implemented and synthetically tested, but no target "
    "POSIX environment, site-packages root, bootstrap module, extension "
    "artifact, shared library, GPU slot or runtime observation exists.")
NEXT_ACTION = (
    "Continue the existing saved-only diagnostic, no new review or variant. "
    "Retry server-4 once at/after " + RETRY + ". If reachable, run "
    "dependency_collection_plan_20260921 with the reviewed server-4 seed and "
    "an observed target CUDA version to materialize one explicit plan; then "
    "run dependency_observation_collector_20260921 and validate the exact "
    "observation with dependency_provenance_audit_20260921; inspect M197 "
    "checkpoint/optimizer/epoch/paths. If unreachable, keep this stage "
    "blocked; do not duplicate the plan-materializer tests or fixture "
    "cross-check. Do not assert target paths, ABI, loader resolution or "
    "runtime equivalence. Only after verified host, held GPU0/1 slot, "
    "dependency/asset/isolation receipts and 3 artifacts/6 data hashes may "
    "saved3040/3893 collation advance; then export3921/4278 retaining31. "
    "Never regenerate recovered groups or run legacy server-6/GPU7 CLI.")
UNBLOCK = (
    "Verified authorized server-4 runtime; reviewed seed materializes one "
    "collector plan under the target interpreter; collector output validates "
    "against dependency_provenance_audit_20260921; independently verified "
    "runtime loader/ABI boundary; held GPU0/1 slot; assets and Linux "
    "isolation. M197 separately requires read-only checkpoint, optimizer, "
    "epoch/path and safe-resume admission.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != SNAPSHOT
            or EXECUTABLE_DUE not in context["research_work"]["due_ids"]):
        raise ValueError("Wrong event snapshot")
    decision = (ROOT / args.decision).resolve()
    if (not decision.is_relative_to(ROOT / "pipeline/decisions")
            or not decision.is_file()):
        raise ValueError("Missing decision")
    if (ROOT / REPORT).exists():
        raise ValueError("Report already exists")

    prior = read(PRIOR)
    modules = list(prior["validation"]["modules"])
    modules.append("test_dependency_collection_plan_20260921")
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Regression failed")

    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    paths = [
        PRIOR,
        args.decision,
        "pipeline/goal.json",
        "SERVERS.yaml",
        "scripts/dependency_collection_plan_20260921.py",
        "scripts/test_dependency_collection_plan_20260921.py",
        "scripts/dependency_observation_collector_20260921.py",
        "scripts/test_dependency_observation_collector_20260921.py",
        "scripts/dependency_provenance_audit_20260921.py",
        SEED,
    ]
    evidence = [
        dict(path=path, sha256=file_sha256(ROOT / path)) for path in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1,
        generated_at=now,
        snapshot_generated_at=context["generated_at"],
        resumed_due_ids=[EXECUTABLE_DUE],
        blocked_due_ids=[
            value for value in context["research_work"]["due_ids"]
            if value != EXECUTABLE_DUE],
        evidence=evidence,
        connectivity=dict(
            server="server-4",
            attempts=1,
            source="direct_ssh_retry",
            preflight_reachable=False,
            direct_retry=False,
            failure="Connection refused on port 22",
            retry_after=RETRY,
            runtime_verified=False,
            gpu_occupancy_verified=False,
            roots_observed=False),
        plan_materializer=dict(
            seed=SEED,
            contract="installed-dependency-collection-seed-v1",
            script="scripts/dependency_collection_plan_20260921.py",
            test="scripts/test_dependency_collection_plan_20260921.py",
            new_tests=6,
            seed_schema_validated=True,
            target_runtime_plan_built=False,
            target_runtime_is_posix=False,
            target_paths_observed=False,
            target_packages_imported=False,
            native_extension_executed=False,
            abi_compatibility_checked=False,
            runtime_loader_resolution_verified=False,
            native_execution_completed=False,
            scientific_validation_complete=False,
            admission=False),
        completed_work=[
            "Retried server-4 once; SSH refused port 22.",
            "Added a stdlib-only target-runtime plan materializer for the dependency collector.",
            "Derived environment and site-packages roots from the target interpreter instead of guessing them.",
            "Selected the exact target extension suffix and rejected missing target artifacts.",
            "Confined site-packages, bootstrap modules and the extension artifact to their declared roots.",
            "Added a reviewed server-4 seed with explicit roots and repository-relative bootstrap identities.",
            "No target path or package was recorded as observed and no queue, GPU or experiment state changed."],
        validation=dict(
            tests_run=result.testsRun,
            tests_passed=result.testsRun - len(result.skipped),
            new_tests=6,
            modules=modules,
            skipped=[dict(test=str(test), reason=reason)
                     for test, reason in result.skipped],
            output=stream.getvalue(),
            target_runtime_plan_built=False,
            target_paths_observed=False,
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
        next_action=NEXT_ACTION,
        retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "The materializer ran only against synthetic Windows fixtures; its POSIX CLI boundary was not executed.",
            "The reviewed seed is a plan input, not evidence that any target path exists.",
            "No target Python, site-packages, package metadata, extension ELF or shared library was read.",
            "The exact target CUDA version remains unobserved and must be supplied explicitly before collection.",
            "No sandbox, GPU slot, assets, data, backward, resources or admission evidence exists."])

    write_new(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    work = read("pipeline/research_work.json")
    candidate = next(
        row for row in work["candidates"] if row["id"] == EXECUTABLE_DUE)
    merged = {item["path"]: item for item in candidate["evidence"]}
    merged.update({item["path"]: item for item in evidence + [entry]})
    candidate.update(
        stage="blocked",
        evidence=list(merged.values()),
        blocker=BLOCKER,
        retry_after=RETRY,
        next_action=NEXT_ACTION,
        unblock_condition=UNBLOCK,
        latest_progress=(
            now + ": target-runtime dependency plan materializer implemented "
            "and synthetically tested; server-4 SSH again refused port22."))
    candidate["dependency_plan_progress"] = dict(
        timestamp=now,
        report=REPORT,
        report_sha256=entry["sha256"],
        tests_passed=report["validation"]["tests_passed"],
        tests_skipped=len(result.skipped),
        target_runtime_plan_built=False,
        target_paths_observed=False,
        native_execution_completed=False,
        scientific_validation_complete=False,
        alternatives_attempted=(
            "One direct SSH retry refused port 22. Implemented and tested "
            "target-runtime plan materialization rather than repeating the "
            "completed collector/validator fixture."))
    work["last_event_tick"] = dict(
        timestamp=now,
        mode="event",
        due_ids=sorted(context["research_work"]["due_ids"]),
        evidence=[entry],
        next_action=NEXT_ACTION,
        result=(
            "Target-runtime plan materializer and reviewed seed added; "
            "server-4 remains unreachable and no queue changed."))
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.dependency_plan_1915.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
