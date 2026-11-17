"""Persist bounded physical-inventory implementation; native gates remain false."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


PRIOR = "pipeline/reports/gpu_validation_progress_20260921-0715.json"
REPORT = "pipeline/reports/gpu_inventory_progress_20260921-0815.json"
RETRY = "2026-09-21T09:07:00+08:00"
NEXT = (
    "Continue the existing saved diagnostic without new variants/reviews. "
    "Physical nvidia-smi inventory collection now has bounded subprocess, "
    "executable hash/path, host stability and strict XML checks. Logical CUDA "
    "identity remains unobserved: next implement the separate in-child logical "
    "UUID observation after pinned dependency/ABI checks and before model load; "
    "test mismatch/failure ordering and reuse validate_gpu_runtime. Do not infer "
    "logical mapping from CUDA_VISIBLE_DEVICES or treat observations as reservation. "
    "Retry server-4 once at/after " + RETRY + ". On reachable host verify actual "
    "runtime/paths, held GPU0/1 slot, executable/PointNet2/native ABI/assets/"
    "checkpoint and Linux isolation. Verify3 artifacts/6 data hashes; collate "
    "saved3040/3893 then exact replay; export3921/4278 retaining full31. Never "
    "regenerate recovered groups or use legacy server-6/GPU7 CLI.")
BLOCKER = (
    "One scheduled server-4 SSH attempt refused port22; no remote command ran. "
    "Runtime/GPU/destination/checkpoint/assets/native ABI/isolation unverified. "
    "Physical collector tests use synthetic XML and mocked host/process observations; "
    "no native logical CUDA observation, production execution callback or authorization.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-21T00:07:08.362698+00:00"):
        raise ValueError("Wrong event snapshot")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Decision missing")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_gpu_inventory_20260921"] + read(PRIOR)["validation"]["modules"]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Regression failed; state not advanced")
    migration = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for row in read(migration)["evidence"]:
        if file_sha256(ROOT / row["path"]) != row["sha256"]:
            raise ValueError("Original migration evidence drift")
    paths = [
        PRIOR, migration, args.decision, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/saved_physical_location_20260920.py",
        "scripts/test_gpu_inventory_20260921.py",
        "scripts/cpu_diagnostic_bootstrap_20260920.py",
        "scripts/bounded_collation_process_20260921.py",
        "scripts/persist_gpu_inventory_tick_20260921.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=1,
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            evidence_basis="Observed exec_command this tick; no scripted retry",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(
            tests_run=result.testsRun, tests_passed=result.testsRun-len(result.skipped),
            new_tests=20, modules=modules,
            skipped=[dict(test=str(t), reason=r) for t, r in result.skipped],
            output=stream.getvalue(), native_data_loaded=False),
        completed_work=[
            "Added physical GPU inventory parser/collector in existing location module.",
            "Reused host observer/validator and bounded_process; no new launcher or CLI.",
            "Explicit GPU0/1 selection; expected full UUID must match returned inventory.",
            "Hash-check explicit nvidia-smi executable before/after bounded read-only command.",
            "Count every listed process, including graphics; unsupported/missing data fail closed.",
            "Runtime stability, bounded time, output digest and finite measurements checked.",
            "Twenty synthetic XML/collection tests; logical CUDA identity remains unobserved."],
        physical_bindings_verified=9, physical_bindings_missing=22,
        registry_denominator=31, model_geometry_captures=0,
        native_execution_completed=False, scientific_validation_complete=False,
        physical_gpu_collector_implemented=True, logical_gpu_collector_implemented=False,
        production_execution_validator_implemented=False,
        admission=False, training_launch=False, checkpoint_transfer=False,
        queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "No actual NVIDIA XML/driver compatibility verified; fixtures synthetic.",
            "Listed-process observation is not complete external-job ownership or reservation.",
            "Binary hashes do not attest shared libraries or prevent hostile host races.",
            "Logical CUDA identity needs a separate native dependency-gated observation.",
            "Native forward/backward, resources, efficacy and novelty remain unverified.",
            "Shared M95 diagnostic implementation does not recover M197 checkpoints."])
    work = read("pipeline/research_work.json")
    due = set(context["research_work"]["due_ids"])
    if due != {c["id"] for c in work["candidates"] if c["id"] in due}:
        raise ValueError("Missing due candidate")
    write_new(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    for candidate in work["candidates"]:
        if candidate["id"] not in due:
            continue
        merged = {e["path"]: e for e in candidate["evidence"]}
        merged.update({e["path"]: e for e in evidence + [entry]})
        candidate.update(
            evidence=list(merged.values()), blocker=BLOCKER, retry_after=RETRY,
            unblock_condition="Observed authorized server-4 runtime/GPU UUID/occupancy "
                "with held slot; verified sources/assets/checkpoint/native ABI/"
                "destination bytes and Linux isolation. Separate logical CUDA observation "
                "must agree. M197 needs optimizer/epoch/path checks and safe resume admission.",
            next_action=NEXT,
            latest_progress=now + ": Physical inventory collector tested; physical9/model0 unchanged.")
        candidate["gpu_inventory_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(result.skipped),
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; physical observation collector "
                "implementation and20 synthetic tests plus bounded regression.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/"
                "GPU0/1 before read-only M197 checkpoint recovery; validate optimizer/"
                "epoch/paths and safe resume admission. Preserve stopped_unknown; "
                "no server-6 restart. Shared M95 diagnostic tests do not recover M197.")
            candidate["latest_progress"] = now + ": SSH refused; M197 recovery blocked."
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(due), evidence=[entry],
        next_action=NEXT, result="Physical inventory collector tested; native blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.gpu_inventory_0815.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
