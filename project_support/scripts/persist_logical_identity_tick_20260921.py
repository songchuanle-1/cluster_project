"""Record logical observer implementation without promoting native admission."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


PRIOR = "pipeline/reports/gpu_inventory_progress_20260921-0815.json"
REPORT = "pipeline/reports/logical_identity_progress_20260921-0912.json"
RETRY = "2026-09-21T10:07:00+08:00"
BLOCKER = (
    "One scheduled SSH attempt to server-4 refused port22; no remote command ran. "
    "Native runtime, dependency ABI, logical CUDA identity, destination data, "
    "checkpoint/assets and Linux isolation remain unverified. Observer tests are "
    "synthetic; trusted dependency loader and held GPU slot are not implemented "
    "by the observer and do not follow from successful unit tests.")
NEXT = (
    "Continue the existing saved diagnostic, without a new variant/review. "
    "Logical identity observer is now implemented and synthetically tested. "
    "Next audit the exact pinned native dependency import sequence for CUDA "
    "initialization side effects and define the trusted dependency-loader "
    "contract from the existing model/dependency inventories; do not claim ABI "
    "verification from static imports. Reuse the observer in the existing driver "
    "execution_check only after that boundary is verified; no wrapper launcher. "
    "Retry server-4 once at/after " + RETRY + ". When reachable, verify runtime/"
    "paths, held GPU0/1 slot, dependency/executable/asset bytes and native ABI; "
    "exercise physical/logical UUID agreement inside the bounded child before "
    "model allocation. Verify3 artifacts/6 data hashes; collate saved3040/3893 "
    "and exact replay, then export3921/4278 with full31 denominator. Never "
    "regenerate recovered groups or run legacy server-6/GPU7 CLI.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-21T01:07:08.807043+00:00"):
        raise ValueError("Wrong event snapshot")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Decision missing")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_logical_gpu_identity_20260921"] + read(PRIOR)["validation"]["modules"]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Regression failed; durable state not advanced")
    migration = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for row in read(migration)["evidence"]:
        if file_sha256(ROOT / row["path"]) != row["sha256"]:
            raise ValueError("Original migration evidence drift")
    paths = [
        PRIOR, migration, args.decision, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/saved_physical_location_20260920.py",
        "scripts/test_logical_gpu_identity_20260921.py",
        "scripts/cpu_diagnostic_bootstrap_20260920.py",
        "scripts/persist_logical_identity_tick_20260921.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now,
        snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=1,
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            evidence_basis="Observed exec_command this tick; no scripted retry",
            runtime_verified=False, gpu_occupancy_verified=False),
        source_check=dict(
            repository="pytorch/pytorch", version="v2.7.1",
            path="torch/csrc/cuda/Module.cpp",
            method="Official source fetched this tick; inspected UUID binding",
            finding="CUuuid.__str__ returns bare 8-4-4-4-12 hex UUID; device "
                    "properties bind uuid except FBCODE_CAFFE2 build. Unsupported "
                    "representations/missing field fail closed.",
            installed_host_version_verified=False),
        validation=dict(
            tests_run=result.testsRun, tests_passed=result.testsRun-len(result.skipped),
            new_tests=20, focused_tests_passed=52, modules=modules,
            skipped=[dict(test=str(t), reason=r) for t, r in result.skipped],
            output=stream.getvalue(), native_data_loaded=False),
        completed_work=[
            "Implemented separate in-child logical identity observer in existing module.",
            "Host/physical capacity/full UUID checked before trusted dependency loader.",
            "Loader precedes all CUDA calls; preinitialized/CPU/ROCm builds rejected.",
            "Observed CUDA properties UUID independently matched to physical inventory.",
            "Reused validate_gpu_runtime; runtime drift and stale capacity fail closed.",
            "Twenty synthetic tests cover ordering, mismatch, native errors and snapshots."],
        physical_bindings_verified=9, physical_bindings_missing=22,
        registry_denominator=31, model_geometry_captures=0,
        native_execution_completed=False, scientific_validation_complete=False,
        logical_gpu_collector_implemented=True,
        production_execution_validator_implemented=False,
        admission=False, training_launch=False, checkpoint_transfer=False,
        queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Tests use a synthetic CUDA facade; no local native imports or allocation.",
            "Trusted dependency loader is caller-owned; no production ABI verifier.",
            "CUDA context initialization can allocate/block; caller must bound child lifetime.",
            "Capacity is observed before context initialization; slot must remain held.",
            "Pinned upstream API inspection does not verify installed Torch/driver support.",
            "No native forward/backward, resources, efficacy or admission evidence.",
            "Shared M95 diagnostic implementation does not recover M197."])
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
            unblock_condition="Authorized server-4 runtime, held GPU0/1 slot and "
                "fresh physical/logical UUID agreement; verified pinned dependency "
                "loader, native ABI, source/assets/checkpoint/destination hashes and "
                "Linux isolation. M197 additionally needs optimizer/epoch/path "
                "verification and safe resume admission.",
            next_action=NEXT,
            latest_progress=now + ": Logical identity observer tested; physical9/model0 unchanged.")
        candidate["logical_identity_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"],
            tests_skipped=len(result.skipped), native_execution_completed=False,
            scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; upstream source inspection and "
                "20 synthetic observer tests plus bounded regression.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/"
                "GPU0/1 before read-only M197 checkpoint recovery; validate optimizer/"
                "epoch/paths and safe resume admission. Preserve stopped_unknown; "
                "no server-6 restart. Shared M95 diagnostic tests do not recover M197.")
            candidate["latest_progress"] = now + ": SSH refused; M197 recovery blocked."
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(due), evidence=[entry],
        next_action=NEXT, result="Logical identity observer tested; native blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.logical_identity_0912.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
