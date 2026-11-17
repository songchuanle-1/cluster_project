"""Persist bounded synthetic preparation evidence, preserving research stages."""
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


PRIOR = "pipeline/reports/bounded_process_progress_20260921-0015.json"
REPORT = "pipeline/reports/host_preparation_progress_20260921-0115.json"
DECISION = "pipeline/decisions/20260921-011236_other.md"
RETRY = "2026-09-21T02:07:00+08:00"
NEXT = (
    "Continue the same saved-only diagnostic: define and test the finite external "
    "dependency/constructor-asset inventory required before executing the prepared "
    "handoff. Preparation returns exact sandbox argv/private scratch but deliberately "
    "does not launch. Connect to complete_handoff only after verified dependencies "
    "and independent original binding/full31 digest/saved indices. Validate actual "
    "Linux process-group cleanup and bwrap enforcement on authorized server-4. "
    "Then implement separate location-aware prepare_replay. Retry server-4 once "
    "at/after " + RETRY + "; verify project_cluster interpreter, code/data/work paths "
    "and GPU0/1 occupancy before transfer/native work. Verify3 artifacts/6 data "
    "hashes plus constructor assets; collate saved3040/3893 then export3921/4278 "
    "retaining full31. Never regenerate saved groups. Local static/synthetic only.")
BLOCKER = (
    "One scheduled server-4 SSH attempt refused port22. Actual runtime/GPU occupancy, "
    "destination bytes, bwrap/kernel support and dependency inventory remain unverified. "
    "Host preparation tests are synthetic, not native diagnostic or checkpoint recovery.")


def main():
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T17:07:07.895462+00:00"):
        raise ValueError("Wrong tick")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_prepare_collation_handoff_20260921"] + read(PRIOR)["validation"]["modules"]
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
        PRIOR, migration, DECISION, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/prepare_collation_handoff_20260921.py",
        "scripts/test_prepare_collation_handoff_20260921.py",
        "scripts/persist_host_preparation_tick_20260921.py",
        "scripts/scratch_collation_launch_20260920.py",
        "scripts/bounded_collation_process_20260921.py",
    ]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=1,
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            command="ssh -o BatchMode=yes -o ConnectTimeout=10 -o ConnectionAttempts=1 songcl@192.168.1.137 hostname",
            evidence_basis="Observed exec_command this tick; no scripted retry",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(
            tests_run=tests.testsRun, tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            modules=modules, new_tests=12, output=stream.getvalue(),
            host_observations_mocked=True, command_construction_mocked_in_new_tests=True,
            native_data_loaded=False, bubblewrap_execution=False,
            linux_process_group_test_executed=False),
        completed_work=[
            "Internal preparation validates observed runtime using existing validator.",
            "Independently supplied executable/bwrap/bootstrap/producer manifest pins checked before and after provisioning.",
            "Fresh private scratch output/tmp/home/cache and read-only probe sentinel provisioned.",
            "Returns existing collation command/run; does not execute or expose a native CLI.",
            "Failure preserves owned scratch and foreign collision paths; no unsandboxed fallback.",
            "Twelve new synthetic host/filesystem tests and full bounded regression.",
            "Original migration evidence rehashed; queue unchanged."],
        registry_denominator=31, physical_bindings_verified=9, physical_bindings_missing=22,
        model_geometry_captures=0, host_preparation_implemented=True,
        host_launch_orchestration_completed=False, native_cli_completed=False,
        scratch_write_enforcement_verified=False, destination_bytes_verified=False,
        external_dependency_attestation=False, relocated_replay_completed=False,
        native_cpu_execution=False, native_gpu_execution=False, checkpoint_transfer=False,
        training_tree_sync=False, training_launch=False, admission=False,
        scientific_validation_complete=False, queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Preparation is not scientific diagnosis, efficacy or admission.",
            "Linux host observation and argv construction mocked in new integration tests.",
            "Existing lower-level static command and subprocess tests cover separate contracts.",
            "No complete preparation-to-native execution integration or public native CLI.",
            "Actual POSIX ownership/mode, process groups, mounts and native packages unverified.",
            "Manifest pins are not full external-dependency attestation.",
            "Shared preparation does not advance M197 checkpoint recovery.",
            "No hostile-host race protection; retained failed scratch needs later bounded cleanup."])
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
            unblock_condition="Verified authorized server-4 runtime/GPU/bwrap/kernel, "
                "destination bytes and external dependencies before native saved collation. "
                "M197 separately needs compatible checkpoint and safe resume admission.")
        candidate["host_preparation_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(tests.skipped),
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; synthetic host preparation and "
                "private scratch failure regression; no unauthorized native work.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/GPU0/1 "
                "before read-only M197 last.pth retrieval; validate optimizer/epoch/path "
                "compatibility before safe resume admission. Preserve stopped_unknown; "
                "no server-6 restart. Shared preparation is not checkpoint recovery.")
            candidate["latest_progress"] = now + ": SSH refused; checkpoint recovery blocked."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = (
                now + ": Host preparation tested synthetically; physical9/model0 unchanged.")
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Missing due record")
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(found), evidence=[entry],
        next_action=NEXT, result="Synthetic host preparation tested; native access blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.host_preparation_0115.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
