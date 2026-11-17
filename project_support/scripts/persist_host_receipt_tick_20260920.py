"""Persist bounded synthetic receipt verification; never admit native work."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


REPORT = "pipeline/reports/host_receipt_progress_20260920-2315.json"
PRIOR = "pipeline/reports/scratch_launch_progress_20260920-2215.json"
RETRY = "2026-09-21T00:07:00+08:00"
NEXT = (
    "Continue saved-only diagnostic: connect collation_command and verify_completion "
    "to verified host/runtime/bwrap checks, fresh private scratch provisioning and "
    "bounded subprocess completion; no unsandboxed fallback or public native CLI "
    "until external dependency/asset attestation is complete. Add location-aware "
    "prepare_replay. Retry server-4 once at/after " + RETRY + "; verify actual "
    "project_cluster executable, code/data/work paths and GPU0/1 occupancy before "
    "transfer/native work. Verify3 original artifacts/6 data hashes plus constructor "
    "assets, collate exact3040/3893, then export3921/4278 retaining full31; never "
    "regenerate saved groups. Real same-child probe must precede native imports; "
    "GPU forwards require coordinated capacity. Local static/synthetic work only.")
BLOCKER = (
    "Server-4 SSH port22 refused on this tick's single scheduled attempt. Runtime, "
    "GPU occupancy, destination bytes and bwrap/kernel support remain unknown. "
    "Host receipt byte validation implemented synthetically; launch orchestration, "
    "native dependency attestation and relocated replay remain incomplete.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T15:07:07.945655+00:00"):
        raise ValueError("Wrong tick context")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Current decision required")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_host_collation_receipts_20260920"] + read(PRIOR)["validation"]["modules"]
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
    paths = [PRIOR, migration, args.decision, "pipeline/goal.json", "SERVERS.yaml",
             "scripts/scratch_collation_launch_20260920.py",
             "scripts/test_host_collation_receipts_20260920.py",
             "scripts/persist_host_receipt_tick_20260920.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(server="server-4", attempts=1, returncode=1,
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            command="ssh -o BatchMode=yes -o ConnectTimeout=10 -o ConnectionAttempts=1 songcl@192.168.1.137 hostname",
            evidence_basis="Observed exec_command this tick, no scripted reattempt",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(
            tests_run=tests.testsRun, tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            modules=modules, new_tests=19, output=stream.getvalue(),
            receipt_files_synthetic=True, native_data_loaded=False,
            bubblewrap_execution=False),
        completed_work=[
            "Read-only host verifier requires successful child exit and matching published JSON receipts.",
            "Independent original binding, full registry digest and exact saved indices required.",
            "Checks sentinel/probe bytes, exact artifact paths, sizes, hashes and final finite inventory.",
            "Rejects missing/duplicate/redirected/hardlinked output and gate flag promotion.",
            "No native tensors deserialized; failures preserve diagnostic outputs.",
            "Original migration evidence rehashed and queue hash preserved."],
        registry_denominator=31, physical_bindings_verified=9, physical_bindings_missing=22,
        model_geometry_captures=0, host_receipt_verifier_implemented=True,
        host_launch_orchestration_completed=False, native_cli_completed=False,
        scratch_write_enforcement_verified=False, destination_bytes_verified=False,
        external_dependency_attestation=False, relocated_replay_completed=False,
        native_cpu_execution=False, native_gpu_execution=False, checkpoint_transfer=False,
        training_tree_sync=False, training_launch=False, admission=False,
        scientific_validation_complete=False, queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Synthetic file identity tests do not establish tensor semantics or native execution.",
            "Self-reported PID/probe fields are not independent process/runtime attestation.",
            "Subprocess launch/provisioning not wired to receipt verification.",
            "All host/native/scientific admission gates remain unpassed.",
            "No protection against actively hostile concurrent filesystem mutation.",
            "Shared diagnostic evidence does not recover M197 checkpoints."])
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
        candidate.update(evidence=list(merged.values()), retry_after=RETRY, blocker=BLOCKER,
            unblock_condition="Verified authorized host/runtime/GPU/bwrap, destination bytes, "
                "external dependencies and native saved collation. M197 separately requires "
                "checkpoint compatibility and safe resume admission.")
        candidate["host_receipt_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(tests.skipped),
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal;19 synthetic on-disk receipt tests and "
                "bounded regression, no native data or unauthorized host execution.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/GPU0/1 "
                "before read-only M197 last.pth retrieval; validate optimizer/epoch/path "
                "compatibility before safe resume admission. Preserve stopped_unknown; "
                "no server-6 restart. Shared receipt tests are not checkpoint recovery.")
            candidate["latest_progress"] = now + ": SSH refused; checkpoint recovery blocked."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = (
                now + ": Host receipt verifier tested synthetically; physical9/model0 unchanged.")
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Missing due record")
    work["last_event_tick"] = dict(timestamp=now, mode="event", due_ids=sorted(found),
        evidence=[entry], next_action=NEXT,
        result="Host receipt byte verification tested; native host access blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.host_receipt_2315.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
