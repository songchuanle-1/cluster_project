"""Persist pinned launcher evidence without promoting native execution gates."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


REPORT = "pipeline/reports/pinned_launcher_progress_20260921-1315.json"
PRIOR = "pipeline/reports/preidentity_handoff_progress_20260921-1215.json"
RETRY = "2026-09-21T14:07:00+08:00"
BLOCKER = (
    "One scheduled server-4 SSH retry refused port22. No remote command ran; "
    "runtime, GPU occupancy, installed dependency bytes/ABI, assets and Linux "
    "isolation remain unverified. Synthetic launcher tests are not native validation.")
NEXT = (
    "Continue the existing diagnostic, no new review or variant. Implement and "
    "test a pinned production driver plus external execution validator that supplies "
    "real held-slot and execution checks to PreIdentityHandoff, using synthetic "
    "children until the authorized host is verified. On that host, inventory "
    "installed dependency/bootstrap roots and extension shared-library provenance "
    "without asserting ABI from hashes. Retry server-4 once at/after " + RETRY + ". "
    "With verified host, held GPU0/1 slot, dependency/assets/isolation and3 "
    "artifacts/6 data hashes, collate saved3040/3893 and exact replay, then export "
    "3921/4278 retaining31. Never regenerate recovered groups or run legacy "
    "server-6/GPU7 CLI.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-21T05:07:06.443580+00:00"):
        raise ValueError("Wrong event snapshot")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Missing decision")
    if (ROOT / REPORT).exists():
        raise ValueError("Report already exists")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    prior = read(PRIOR)
    modules = ["test_pinned_bootstrap_launcher_20260921"] + prior["validation"]["modules"]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Regression failed")
    paths = [
        PRIOR, args.decision, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/pinned_diagnostic_imports_20260920.py",
        "scripts/preidentity_handoff_20260921.py",
        "scripts/pinned_bootstrap_launcher_20260921.py",
        "scripts/test_pinned_bootstrap_launcher_20260921.py",
        "scripts/bounded_collation_process_20260921.py",
        "scripts/persist_pinned_launcher_tick_20260921.py",
    ]
    evidence = [dict(path=path, sha256=file_sha256(ROOT / path)) for path in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now,
        snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=255,
            command=("ssh -o BatchMode=yes -o ConnectTimeout=8 "
                     "-o ConnectionAttempts=1 songcl@192.168.1.137 hostname"),
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            evidence_basis="Observed exec_command this tick; no scripted retry",
            runtime_verified=False, gpu_occupancy_verified=False),
        completed_work=[
            "Added a fresh-bundle producer with an exact canonical source manifest.",
            "The isolated child runs a hash-pinned launcher file as __main__ under -I -B -S.",
            "Manifest, handoff, context, executable and driver entrypoint pins are rechecked.",
            "The child loads PinnedDiagnosticImports from bytes, constructs PreIdentityHandoff and invokes a pinned driver.",
            "Whole-child execution has wall-time and combined-output bounds with no retry.",
            "One write-once JSON result is parent-verified for hash, contract and positive claims.",
            "Thirteen focused launcher tests and the bounded regression passed synthetically.",
            "No model/native execution, queue mutation, checkpoint transfer, resources or admission."],
        validation=dict(
            tests_run=result.testsRun,
            tests_passed=result.testsRun - len(result.skipped),
            new_tests=13, modules=modules,
            skipped=[dict(test=str(test), reason=reason)
                     for test, reason in result.skipped],
            output=stream.getvalue(), native_data_loaded=False),
        physical_bindings_verified=9, physical_bindings_missing=22,
        registry_denominator=31, model_geometry_captures=0,
        native_execution_completed=False, scientific_validation_complete=False,
        native_backward_verified=False, resources_verified=False,
        admission=False, training_launch=False, checkpoint_transfer=False,
        queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "The launcher proves pinned source bytes and isolated startup, not sandbox enforcement.",
            "Executable hashing and spawning remain separate operations; fd-based exec is not implemented.",
            "Installed dependency and extension shared-library provenance/ABI remain unverified.",
            "Only a synthetic driver is tested; the production held-slot and execution validator is absent.",
            "Whole-child CPU and private scratch limits are not supplied by bounded_process.",
            "No actual GPU identity, native forward/backward/resources/efficacy or admission evidence.",
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
            evidence=list(merged.values()), blocker=BLOCKER, retry_after=RETRY,
            next_action=NEXT,
            unblock_condition=(
                "Verified authorized server-4 runtime, held GPU0/1 slot, pinned "
                "production driver/validator, installed dependency/shared-library "
                "provenance, assets and Linux isolation. M197 separately requires "
                "checkpoint/optimizer/epoch/path and resume admission."),
            latest_progress=(
                now + ":pinned launcher producer/runtime implemented and tested synthetically."))
        candidate["pinned_launcher_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"],
            tests_skipped=len(result.skipped), native_execution_completed=False,
            scientific_validation_complete=False,
            alternatives_attempted=(
                "One SSH refusal;13 new synthetic launcher tests plus bounded "
                "regression. No native packages/data or unauthorized hosts."))
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/GPU0/1 "
                "before read-only M197 checkpoint recovery; validate optimizer/epoch/paths "
                "and safe resume admission. Preserve stopped_unknown; no server-6 restart. "
                "Shared M95 loader does not recover M197.")
            candidate["latest_progress"] = now + ":SSH refused; M197 recovery blocked."
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(due), evidence=[entry],
        next_action=NEXT,
        result=("Pinned launcher/bootstrap producer implemented and tested "
                "synthetically; native work remains blocked."))
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.pinned_launcher_1315.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
