"""Record synthetic process integration without scientific gate promotion."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


PRIOR = "pipeline/reports/host_receipt_progress_20260920-2315.json"
REPORT = "pipeline/reports/bounded_process_progress_20260921-0015.json"
RETRY = "2026-09-21T01:07:00+08:00"
NEXT = (
    "Continue existing saved-only diagnostic: integrate bounded_process and "
    "complete_handoff with collation_command, verified host/runtime/bwrap and "
    "fresh private scratch provisioning. No public native CLI until external "
    "dependency/asset attestation is complete; no unsandboxed fallback. Validate "
    "Linux process-group cleanup on the authorized host. Then implement separate "
    "location-aware prepare_replay. Retry server-4 once at/after " + RETRY + "; "
    "verify actual project_cluster executable, code/data/work paths and GPU0/1 "
    "occupancy before transfer/native work. Verify3 original artifacts/6 data "
    "hashes plus constructor assets; collate saved3040/3893 then export3921/4278 "
    "retaining full31. Never regenerate saved groups. Local static/synthetic only.")
BLOCKER = (
    "Single scheduled server-4 SSH attempt refused port22. Runtime/GPU occupancy, "
    "destination bytes, bwrap/kernel and external dependencies remain unverified. "
    "Bounded subprocess/receipt handoff is synthetic-only and does not resolve "
    "native diagnostic execution or M197 checkpoint recovery.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T16:07:07.267436+00:00"):
        raise ValueError("Wrong tick")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Current decision required")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_bounded_collation_process_20260921"] + read(PRIOR)["validation"]["modules"]
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
             "scripts/bounded_collation_process_20260921.py",
             "scripts/test_bounded_collation_process_20260921.py",
             "scripts/persist_bounded_process_tick_20260921.py",
             "scripts/scratch_collation_launch_20260920.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(server="server-4", attempts=1, returncode=1,
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            command="ssh -o BatchMode=yes -o ConnectTimeout=10 -o ConnectionAttempts=1 songcl@192.168.1.137 hostname",
            evidence_basis="Observed exec_command this tick; no scripted retry",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(
            tests_run=tests.testsRun, tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            modules=modules, new_tests=17, output=stream.getvalue(),
            process_tests_synthetic=True, native_data_loaded=False,
            bubblewrap_execution=False, linux_process_group_test_executed=False),
        completed_work=[
            "Actual synthetic child stdout/stderr drained under one combined byte budget.",
            "Finite timeout kills/reaps immediate child; stdin closed and inherited environment removed.",
            "Linux group cleanup implemented but untested on Windows.",
            "Existing byte receipt verifier wired to bounded subprocess completion.",
            "Actual synthetic child to real on-disk synthetic receipt verification passed.",
            "Nonzero exit, absent artifacts, timeout, oversized output and invalid UTF8 fail closed.",
            "Original migration evidence rehashed; queue unchanged."],
        registry_denominator=31, physical_bindings_verified=9, physical_bindings_missing=22,
        model_geometry_captures=0, subprocess_receipt_handoff_implemented=True,
        host_launch_orchestration_completed=False, native_cli_completed=False,
        scratch_write_enforcement_verified=False, destination_bytes_verified=False,
        external_dependency_attestation=False, relocated_replay_completed=False,
        native_cpu_execution=False, native_gpu_execution=False, checkpoint_transfer=False,
        training_tree_sync=False, training_launch=False, admission=False,
        scientific_validation_complete=False, queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Synthetic integration is not native diagnosis, efficacy or admission.",
            "Generic internal process adapter is not an authorization or sandbox validator.",
            "No native CLI; verified runtime/provisioning and complete attestation still required.",
            "Linux process group and real bubblewrap enforcement not exercised on Windows.",
            "Windows tests cover immediate child only; native work is Linux server-4 only.",
            "Memory/output capture is bounded; this is not a child resource quota.",
            "Shared diagnostics do not recover M197 checkpoints."])
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
        candidate.update(
            evidence=list(merged.values()), retry_after=RETRY, blocker=BLOCKER,
            unblock_condition="Verified authorized server-4 runtime/GPU/bwrap, destination "
                "bytes and external dependencies; real saved collation. M197 separately "
                "needs checkpoint compatibility and safe resume admission.")
        candidate["bounded_process_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(tests.skipped),
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; actual stdlib synthetic subprocess "
                "integration and bounded regression without native data/unauthorized hosts.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/GPU0/1 "
                "before read-only M197 last.pth retrieval; validate optimizer/epoch/path "
                "compatibility before safe resume admission. Preserve stopped_unknown; "
                "no server-6 restart. Shared process tests are not checkpoint recovery.")
            candidate["latest_progress"] = now + ": SSH refused; checkpoint recovery blocked."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = (
                now + ": Bounded process/receipt integration synthetic only; physical9/model0 unchanged.")
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Missing due record")
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(found), evidence=[entry],
        next_action=NEXT, result="Synthetic process/receipt handoff tested; native access blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.bounded_process_0015.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
