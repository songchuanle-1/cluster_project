"""Persist bounded event work; synthetic observations never promote native gates."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from model_execution_inventory_20260921 import boundary_inventory
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


REPORT = "pipeline/reports/gpu_validation_progress_20260921-0715.json"
PRIOR = "pipeline/reports/model_inventory_progress_20260921-0615.json"
RETRY = "2026-09-21T08:07:00+08:00"
NEXT = (
    "Continue existing saved diagnostic, no new variant/review. GPU observation "
    "validation now reuses shared host/path and capacity checks, requires full "
    "UUID physical0/1 to sole logical0 mapping, and preserves CPU CUDA-hidden "
    "validation. Next implement bounded read-only host/device observation "
    "collection in the fresh GPU child and test parsing/failure paths; no "
    "launcher or claimed authorization. Resolve actual PointNet2 package location "
    "and remaining framework.torch relative/private-Torch dependencies on the "
    "authorized host; static17-source audit is not full closure. Retry server-4 "
    "once at/after " + RETRY + ". If reachable verify interpreter/paths, "
    "allocation/held slot, actual UUID/occupancy, native ABI, weights/checkpoint "
    "and Linux enforcement before any data/model load. Verify3 relocated "
    "artifacts/6 data hashes, collate3040/3893 and exact saved replay; then "
    "export3921/4278 retaining31. Never regenerate recovered groups or run "
    "legacy server-6/GPU7 CLI.")
BLOCKER = (
    "One scheduled server-4 SSH attempt refused port22; no remote command ran. "
    "Actual host/GPU/destination bytes/checkpoint/assets/native ABI/isolation "
    "remain unverified. Observation validation is synthetic only, without "
    "native collector, production execution callback or launch authorization.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T23:07:07.675941+00:00"):
        raise ValueError("Wrong event context")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Decision missing")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_gpu_runtime_validation_20260921"] + read(PRIOR)["validation"]["modules"]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Regression failed; durable state not advanced")
    audit = boundary_inventory(ROOT / "Cluster")
    migration = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for row in read(migration)["evidence"]:
        if file_sha256(ROOT / row["path"]) != row["sha256"]:
            raise ValueError("Original migration evidence drift")
    paths = [
        PRIOR, migration, args.decision, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/cpu_diagnostic_bootstrap_20260920.py",
        "scripts/test_cpu_diagnostic_bootstrap_20260920.py",
        "scripts/saved_physical_location_20260920.py",
        "scripts/test_saved_physical_location_20260920.py",
        "scripts/model_execution_inventory_20260921.py",
        "scripts/test_model_execution_inventory_20260921.py",
        "scripts/test_gpu_runtime_validation_20260921.py",
        "scripts/persist_gpu_validation_tick_20260921.py"]
    paths += ["Cluster/" + row["path"] for row in audit["sources"]]
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
            new_tests=14, modules=modules,
            skipped=[dict(test=str(t), reason=r) for t, r in result.skipped],
            output=stream.getvalue(), native_data_loaded=False),
        boundary_inventory=audit,
        completed_work=[
            "Shared host/path validator extracted; CPU CUDA-hidden validation preserved.",
            "GPU observation validation added to existing location/capacity module.",
            "Require independently agreeing full UUID, physical0/1 and sole logical0.",
            "Reuse fresh idle capacity and coordinated-slot requirement; no reservation.",
            "Twelve GPU synthetic tests and two boundary audit tests added.",
            "Seventeen explicit actual framework dependency files audited without imports.",
            "Recorded absent inspected PointNet2 paths and unresolved installed location."],
        physical_bindings_verified=9, physical_bindings_missing=22,
        registry_denominator=31, model_geometry_captures=0,
        native_execution_completed=False, scientific_validation_complete=False,
        production_execution_validator_implemented=False,
        gpu_observation_validation_implemented=True, native_gpu_collector_implemented=False,
        admission=False, training_launch=False, checkpoint_transfer=False,
        queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"])
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
            unblock_condition="Observed authorized server-4 runtime/UUID/occupancy "
                "with held slot; verified sources/assets/checkpoint/native ABI/"
                "destination bytes and Linux enforcement. M197 independently "
                "requires compatible optimizer/epoch/path and safe resume admission.",
            next_action=NEXT,
            latest_progress=now + ": GPU validator/static boundary audit; physical9/model0 unchanged.")
        candidate["gpu_validation_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(result.skipped),
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; shared host/GPU validation "
                "implementation,17-source static audit,14 new synthetic tests and regression.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/"
                "GPU0/1 before read-only M197 checkpoint recovery; validate optimizer/"
                "epoch/paths and safe resume admission. Preserve stopped_unknown; "
                "no server-6 restart. Shared M95 diagnostic work does not recover M197.")
            candidate["latest_progress"] = now + ": SSH refused; M197 checkpoint recovery blocked."
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(due), evidence=[entry],
        next_action=NEXT, result="GPU observation validation/static audit complete; native blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.gpu_validation_0715.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
