"""Persist static/synthetic handoff integration evidence for the exact event tick."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


PRIOR = "pipeline/reports/dependency_inventory_progress_20260921-0215.json"
REPORT = "pipeline/reports/prepared_execution_progress_20260921-0315.json"
RETRY = "2026-09-21T04:07:00+08:00"
NEXT = (
    "Continue the existing saved diagnostic, not a new mechanism. The internal "
    "prepare_and_complete adapter is synthetically tested; no production execution "
    "validator or native CLI exists. Next implement/test a separate location-aware "
    "prepare_replay consuming exact saved collation receipts/batches and independent "
    "original full31 binding, preserving original producer/provenance and no resampling. "
    "Retry server-4 once at/after " + RETRY + ". On verified access check runtime/"
    "code/data/work paths and GPU0/1 occupancy; measure actual dependencies, extension "
    "ABI/shared libraries, tokenizer assets and nonempty TRAIN listing. Verify3 saved "
    "artifacts/6 data hashes and Linux group cleanup/bwrap enforcement. A real external "
    "execution validator must recheck those gates before using the adapter. Then collate "
    "3040/3893, prepare saved replay, export3921/4278 retaining31. Local static/synthetic "
    "only; never regenerate recovered groups or run unchanged server-6 driver.")
BLOCKER = (
    "One scheduled server-4 SSH attempt refused port22. Runtime/GPU/data/checkpoints/"
    "native dependencies and Linux enforcement remain unverified. Internal handoff "
    "integration is not an execution validator, dependency attestation or checkpoint recovery.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T19:07:07.727714+00:00"):
        raise ValueError("Wrong tick")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Current decision required")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_prepared_collation_execution_20260921"] + read(PRIOR)["validation"]["modules"]
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
        "scripts/prepared_collation_execution_20260921.py",
        "scripts/test_prepared_collation_execution_20260921.py",
        "scripts/persist_prepared_execution_tick_20260921.py",
        "scripts/prepare_collation_handoff_20260921.py",
        "scripts/bounded_collation_process_20260921.py",
        "scripts/scratch_collation_launch_20260920.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=1,
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            command="ssh -o BatchMode=yes -o ConnectTimeout=8 -o ConnectionAttempts=1 "
                "songcl@192.168.1.137 \"hostname; id -un; nvidia-smi "
                "--query-gpu=index,name,memory.used,memory.total,utilization.gpu "
                "--format=csv,noheader; test -d /data/songcl/Project/Cluster_project/Cluster "
                "&& test -d /home/songcl/data/data "
                "&& test -d /data/songcl/Project/Cluster_project/Cluster_checkpoints "
                "&& test -f /home/dl04/anaconda3/etc/profile.d/conda.sh\"",
            evidence_basis="Observed exec_command this tick; no scripted retry",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(
            tests_run=tests.testsRun, tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            modules=modules, new_tests=16, output=stream.getvalue(),
            initial_failure="Windows short temporary path rejected by boundary; fixture "
                "now resolves path, production checks unchanged; 16 focused tests rerun passed.",
            native_data_loaded=False, bubblewrap_execution=False,
            linux_process_group_test_executed=False),
        completed_work=[
            "Single internal adapter connects exact prepared command/run to complete_handoff.",
            "Independent binding/digest/indices frozen before validators and child execution.",
            "Before-prepare and before-launch external validator hooks; copied contracts.",
            "Host pins rechecked after final validator; no retries, fallback or native CLI.",
            "Invalid budgets, expectations, flags, pin drift and failures reject without launch.",
            "Actual stdlib child verified against synthetic on-disk artifacts; mismatched binding rejects.",
            "Sixteen new tests plus bounded regression; original migration evidence rehashed."],
        registry_denominator=31, physical_bindings_verified=9, physical_bindings_missing=22,
        model_geometry_captures=0, production_execution_validator_implemented=False,
        external_dependency_attestation=False, destination_bytes_verified=False,
        native_cli_completed=False, native_cpu_execution=False, native_gpu_execution=False,
        checkpoint_transfer=False, training_tree_sync=False, training_launch=False,
        admission=False, scientific_validation_complete=False, queue_changed=False,
        queue_sha256=queue_hash, blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "A validator callback invocation cannot prove deployment validation; no real validator supplied.",
            "Host preparation mocked in adapter tests; independently covered by existing synthetic tests.",
            "Real subprocess/receipt verification uses only synthetic bytes, not native tensors.",
            "No Linux sandbox, native dependency compatibility, runtime or physical endpoint measured.",
            "Hashes establish identity, not scientific validity; scientific admission unchanged.",
            "M197 checkpoint recovery remains independently blocked; shared adapter is not M197 progress."])
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
            unblock_condition="Verified authorized server-4 runtime/GPU, bwrap/kernel, "
                "destination bytes and actual native dependencies; implement real execution "
                "validator before adapter launch. M197 separately needs compatible checkpoint/safe admission.")
        candidate["prepared_execution_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(tests.skipped),
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; internal handoff integration with "
                "16 synthetic tests plus bounded regression; no unauthorized native work.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/GPU0/1 "
                "before read-only M197 last.pth retrieval; validate optimizer/epoch/path "
                "compatibility before safe resume admission. Preserve stopped_unknown; "
                "no server-6 restart. Shared handoff integration is not checkpoint recovery.")
            candidate["latest_progress"] = now + ": SSH refused; checkpoint recovery blocked."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = now + ": Internal handoff tested; physical9/model0 unchanged."
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Missing due record")
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(found), evidence=[entry],
        next_action=NEXT, result="Internal handoff implemented/tested; native access blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.prepared_execution_0315.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
