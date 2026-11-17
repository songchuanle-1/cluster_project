"""Persist the stdlib-only dependency collector tick without native promotion."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


REPORT = "pipeline/reports/dependency_collector_progress_20260921-1750.json"
PRIOR = "pipeline/reports/dependency_provenance_progress_20260921-1515.json"
RETRY = "2026-09-21T18:45:00+08:00"
BLOCKER = (
    "Server-4 refused SSH port 22 again at 17:44 Asia/Shanghai. The "
    "stdlib-only collector is implemented and synthetically tested, but no "
    "target root, bootstrap module, package file, ELF declaration, shared "
    "library or GPU was observed. ABI, loader resolution, runtime, isolation "
    "and native execution remain unverified.")
GENERAL_NEXT = (
    "Continue the existing saved-only diagnostic, no new review or variant. "
    "Retry server-4 once at/after " + RETRY + ". If reachable, materialize an "
    "explicit collection plan, run dependency_observation_collector_20260921 "
    "in the target interpreter, validate the manifest with "
    "dependency_provenance_audit_20260921, and inspect M197 "
    "checkpoint/optimizer/epoch/paths. If unreachable, cross-check the "
    "collector against the validator using a POSIX fixture only; do not "
    "fabricate host rows or promote local facts. Do not assert ABI, loader "
    "resolution or runtime equivalence. Only after verified host, held GPU0/1 "
    "slot, dependency/asset/isolation receipts and 3 artifacts/6 data hashes "
    "may saved3040/3893 collation advance; then export3921/4278 retaining31. "
    "Never regenerate recovered groups or run legacy server-6/GPU7 CLI.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-21T09:26:18.315015+00:00"):
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
    modules = [
        "test_dependency_observation_collector_20260921",
    ] + prior["validation"]["modules"]
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
        "scripts/persist_dependency_collector_tick_20260921.py",
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
            server="server-4", attempts=1, source="direct_ssh_retry",
            returncode=1,
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            runtime_verified=False, gpu_occupancy_verified=False,
            roots_observed=False),
        collector=dict(
            contract="installed-dependency-observation-v1",
            plan_contract="installed-dependency-collection-plan-v1",
            collector="scripts/dependency_observation_collector_20260921.py",
            collector_sha256=file_sha256(
                ROOT / "scripts/dependency_observation_collector_20260921.py"),
            validator="scripts/dependency_provenance_audit_20260921.py",
            stdlib_only=True,
            model_package_imports=False,
            native_extension_execution=False,
            planned_observations=[
                "runtime executable, Python SOABI/Torch version/CUDA version",
                "environment, code, data, work and site-packages roots",
                "explicit bootstrap modules and exact nine direct packages",
                "package module and metadata SHA256 rows",
                "pointgroup_ops_ext ELF identity and DT_NEEDED declarations",
                "hashed ldconfig-cache candidates for every DT_NEEDED row",
            ],
            observed_host_input=False,
            abi_compatibility_checked=False,
            runtime_loader_resolution_verified=False,
            shared_library_provenance_observed=False,
            native_data_loaded=False,
            external_dependency_attestation=False,
            native_execution_completed=False,
            scientific_validation_complete=False,
            admission=False),
        completed_work=[
            "Added a standalone stdlib-only collector for the validated installed-dependency observation contract.",
            "The collector discovers the exact nine direct distributions and module files without importing them.",
            "It hashes package metadata, explicit bootstrap files, runtime roots and the native extension bytes.",
            "It parses ELF64/ELF32 dynamic sections directly and records DT_NEEDED declarations without executing the extension.",
            "It requires one hashed ldconfig-cache candidate for every declared shared library.",
            "It records CUDA_VISIBLE_DEVICES as observed environment state and rejects absent or duplicate identities.",
            "Synthetic tests cover the ELF parser, cache parser, package discovery, output schema and rejection paths.",
            "No target filesystem, package, ELF, shared library or GPU was observed."],
        validation=dict(
            tests_run=result.testsRun,
            tests_passed=result.testsRun - len(result.skipped),
            new_tests=6,
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
            "The collector is validated only against synthetic packages and ELF data.",
            "No target Python, site-packages, package metadata, extension ELF or system library was read.",
            "The receipt records declarations; it does not prove loaded bytes or linker resolution.",
            "Python SOABI, Torch version and observed CUDA_VISIBLE_DEVICES are facts, not compatibility decisions.",
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
                now + ": stdlib-only dependency observation collector and "
                "synthetic contract tests added; server remains unobserved."))
        candidate["dependency_collector_progress"] = dict(
            timestamp=now,
            report=REPORT,
            report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"],
            tests_skipped=len(result.skipped),
            observed_host_input=False,
            model_package_imports=False,
            native_execution_completed=False,
            scientific_validation_complete=False,
            alternatives_attempted=(
                "Direct server-4 SSH retry refused port22; six new synthetic "
                "collector tests plus bounded regression. No native package, "
                "ELF, data, GPU or host was read."))
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". If reachable, "
                "run the validated stdlib-only collector with an explicit plan, "
                "validate the observation receipt, and inspect M197 "
                "checkpoint/optimizer/epoch/paths; preserve stopped_unknown and "
                "require safe-resume admission before any restart. If "
                "unreachable, cross-check collector and validator schemas with "
                "a POSIX fixture only. No server-6 restart; shared M95 loader "
                "does not recover M197.")
    work["last_event_tick"] = dict(
        timestamp=now,
        mode="event",
        due_ids=sorted(due),
        evidence=[entry],
        next_action=GENERAL_NEXT,
        result=(
            "Stdlib-only dependency observation collector implemented and "
            "tested synthetically; server-4 remains unverified and no queue "
            "changed."))
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.dependency_collector_1750.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
