"""Persist static dependency-provenance evidence without native promotion."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


REPORT = "pipeline/reports/dependency_provenance_progress_20260921-1515.json"
PRIOR = "pipeline/reports/production_execution_progress_20260921-1415.json"
RETRY = "2026-09-21T16:07:00+08:00"
BLOCKER = (
    "Server-4 refused SSH port 22 at 15:07 Asia/Shanghai. The static "
    "observation contract and receipt validator were tested synthetically, "
    "but no target root, bootstrap module, package file, ELF declaration or "
    "shared-library candidate was observed. ABI, loader resolution, runtime, "
    "isolation, GPU and native execution remain unverified.")
GENERAL_NEXT = (
    "Continue the existing saved-only diagnostic, no new review or variant. "
    "Retry server-4 once at/after " + RETRY + ". If reachable, collect the "
    "read-only observation manifest required by "
    "dependency_provenance_audit_20260921 for runtime roots, exact bootstrap "
    "modules, all nine direct package files and pointgroup_ops_ext ELF "
    "declarations/cache candidates, then write and verify the receipt. If "
    "unreachable, implement the stdlib-only collector for that exact schema "
    "without importing model packages. Do not assert ABI, loader resolution or "
    "runtime equivalence. Only after verified host, held GPU0/1 slot, "
    "dependency/asset/isolation receipts and 3 artifacts/6 data hashes may "
    "saved3040/3893 collation advance; then export3921/4278 retaining31. Never "
    "regenerate recovered groups or run legacy server-6/GPU7 CLI.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-21T07:07:07.353003+00:00"):
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
        "test_dependency_provenance_audit_20260921",
    ] + prior["validation"]["modules"]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Regression failed")
    paths = [
        PRIOR, args.decision, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/dependency_provenance_audit_20260921.py",
        "scripts/test_dependency_provenance_audit_20260921.py",
        "scripts/saved_dependency_inventory_20260921.py",
        "scripts/server4_execution_validator_20260921.py",
        "scripts/production_saved_collation_driver_20260921.py",
        "scripts/persist_dependency_provenance_tick_20260921.py",
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
        static_dependency_provenance=dict(
            contract="installed-dependency-provenance-v1",
            observation_contract="installed-dependency-observation-v1",
            validator="scripts/dependency_provenance_audit_20260921.py",
            validator_sha256=file_sha256(
                ROOT / "scripts/dependency_provenance_audit_20260921.py"),
            observed_host_input=False,
            direct_package_count=9,
            native_extension="pointgroup_ops.pointgroup_ops_ext",
            enforced=[
                "canonical POSIX roots and file paths",
                "lowercase SHA256 rows",
                "exact direct-package import-root set",
                "unique nonempty bootstrap inventory",
                "ELF class, byte order and machine recorded",
                "declared NEEDED/cache-candidate set equality",
            ],
            rejected=[
                "duplicate JSON keys and nonfinite values",
                "missing or added direct package roots",
                "duplicate bootstrap or site-packages rows",
                "mismatched shared-library declarations and candidates",
                "any ABI, loader-resolution, runtime or admission promotion",
            ],
            abi_compatibility_checked=False,
            runtime_loader_resolution_verified=False,
            shared_library_provenance_observed=False,
            native_data_loaded=False,
            external_dependency_attestation=False,
            native_execution_completed=False,
            scientific_validation_complete=False,
            admission=False),
        completed_work=[
            "Added a strict static receipt validator for installed dependency and bootstrap provenance.",
            "The validator records canonical roots, bootstrap rows and exact direct-package files.",
            "It records pointgroup_ops_ext ELF class, byte order, machine and declared NEEDED entries.",
            "Every declared shared library requires one hashed ldconfig-cache candidate row.",
            "The schema rejects package drift, duplicate rows, noncanonical paths, duplicate JSON keys and nonfinite values.",
            "The output receipt preserves recorded facts but forces ABI, loader, runtime and admission gates false.",
            "Nine new synthetic tests plus the bounded regression passed.",
            "No server filesystem, installed package, ELF or shared library was observed."],
        validation=dict(
            tests_run=result.testsRun,
            tests_passed=result.testsRun - len(result.skipped),
            new_tests=9,
            modules=modules,
            skipped=[dict(test=str(test), reason=reason)
                     for test, reason in result.skipped],
            output=stream.getvalue(),
            native_data_loaded=False,
            abi_compatibility_checked=False),
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
        next_action=GENERAL_NEXT,
        retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "The observation schema is validated only with synthetic rows.",
            "No target Python, site-packages, package metadata, extension ELF or system library was read.",
            "The receipt records declarations; it does not prove the loaded extension or linker resolution.",
            "Python SOABI/Torch versions are facts, not a compatibility decision.",
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
                "Verified authorized server-4 runtime; a valid static "
                "dependency-provenance receipt with observed roots, bootstrap, "
                "direct package files and extension declarations; independently "
                "verified runtime loader/ABI boundary; held GPU0/1 slot; assets "
                "and Linux isolation. M197 separately requires read-only "
                "checkpoint, optimizer, epoch/path and safe-resume admission."),
            latest_progress=(
                now + ": static dependency/bootstrap/extension observation "
                "contract and receipt validator added and tested synthetically."))
        candidate["dependency_provenance_progress"] = dict(
            timestamp=now,
            report=REPORT,
            report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"],
            tests_skipped=len(result.skipped),
            observed_host_input=False,
            abi_compatibility_checked=False,
            native_execution_completed=False,
            scientific_validation_complete=False,
            alternatives_attempted=(
                "Direct server-4 SSH retry refused port22; nine new static "
                "schema tests plus bounded regression. No native package, ELF, "
                "data or host was read."))
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". If reachable, "
                "first collect the read-only dependency provenance observation "
                "and inspect M197 checkpoint/optimizer/epoch/paths; preserve "
                "stopped_unknown and require safe resume admission before any "
                "restart. If unreachable, implement the stdlib-only collector "
                "for the validated schema. No server-6 restart; shared M95 "
                "loader does not recover M197.")
    work["last_event_tick"] = dict(
        timestamp=now,
        mode="event",
        due_ids=sorted(due),
        evidence=[entry],
        next_action=GENERAL_NEXT,
        result=(
            "Static dependency provenance receipt contract implemented and "
            "tested synthetically; server-4 remains unverified and no queue "
            "changed."))
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.dependency_provenance_1515.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
