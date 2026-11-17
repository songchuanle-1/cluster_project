"""Persist the server-6 runtime observation and checkpoint inspection tick."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = "2026-09-21T13:09:33.541267+00:00"
REPORT = "pipeline/reports/server6_runtime_diagnostic_20260921-2124.json"
EVIDENCE_PATHS = [
    "pipeline/headless/.tick_context.json",
    "pipeline/goal.json",
    "SERVERS.yaml",
    "scripts/dependency_observation_collector_20260921.py",
    "scripts/test_dependency_observation_collector_20260921.py",
    "scripts/dependency_collection_plan_20260921.py",
    "scripts/test_dependency_collection_plan_20260921.py",
    "scripts/dependency_provenance_audit_20260921.py",
    "scripts/test_dependency_provenance_audit_20260921.py",
    "scripts/pointgroup_runtime_smoke_20260921.py",
    "scripts/inspect_m197_checkpoint_20260921.py",
    "pipeline/diagnostic_bundles/dependency_collection_seed_server6_20260921.json",
    "pipeline/diagnostic_bundles/dependency_plan_server6_20260921_v3.json",
    "pipeline/diagnostic_bundles/dependency_observation_server6_20260921_v5.json",
    "pipeline/diagnostic_bundles/dependency_provenance_receipt_server6_20260921.json",
    "pipeline/diagnostic_bundles/pointgroup_runtime_smoke_server6_20260921.json",
    "pipeline/diagnostic_bundles/m197_checkpoint_inspection_server6_20260921.json",
]
NEXT_ACTION = (
    "Continue the existing saved-only diagnostic; do not repeat completed "
    "dependency collection or fixture cross-checks. Verify the exact three "
    "artifact and six data hashes, then exercise the model-loader/import "
    "boundary without loading the full model or starting training. Preserve "
    "M197 as stopped_unknown and require the full safe-resume admission chain "
    "before any restart. Do not regenerate recovered groups or treat the tiny "
    "operator smoke as full-model efficacy evidence.")
LATEST = (
    "2026-09-21T21:24:00+08:00: server-6 dependency provenance passed; "
    "pointgroup_ops imported, tiny operator CUDA forward/backward produced "
    "finite gradients, and M197 checkpoint metadata was inspected.")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_new(path, value, mode=0o600):
    path = ROOT / path
    if path.exists() or path.is_symlink() or not path.parent.is_dir():
        raise ValueError("Fresh output path required: " + str(path))
    encoded = json.dumps(
        value, indent=2, sort_keys=True, allow_nan=False).encode("utf-8")
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return sha256(path)


def replace_json(path, value):
    target = ROOT / path
    descriptor, temp_name = tempfile.mkstemp(
        prefix=target.name + ".", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, target)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    decision = (ROOT / args.decision).resolve()
    if (not decision.is_relative_to(ROOT / "pipeline" / "decisions")
            or not decision.is_file()):
        raise ValueError("Missing decision record")
    if (ROOT / REPORT).exists():
        raise ValueError("Report already exists")

    context = read_json(ROOT / "pipeline/headless/.tick_context.json")
    if (context.get("mode") != "event"
            or context.get("generated_at") != SNAPSHOT):
        raise ValueError("Wrong event snapshot")
    due_ids = sorted(context["research_work"]["due_ids"])
    expected_due = [
        "referent-supervision-axis",
        "referent-causality-audit",
        "modality-identity-preservation",
        "referent-discrimination",
        "instance-identity-representation",
        "referent-query-selection",
        "input-modality-distinguishability",
        "same-target-description-grounding",
    ]
    if due_ids != sorted(expected_due):
        raise ValueError("Unexpected due IDs")

    modules = [
        "test_dependency_observation_collector_20260921",
        "test_dependency_collection_plan_20260921",
        "test_dependency_provenance_audit_20260921",
    ]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Targeted regression failed")

    queue_hash = sha256(ROOT / "pipeline/queue.json")
    work_hash = sha256(ROOT / "pipeline/research_work.json")
    evidence = [
        {"path": path, "sha256": sha256(ROOT / path)}
        for path in EVIDENCE_PATHS
    ]
    now = datetime.now(timezone.utc).astimezone().isoformat()
    report = {
        "schema_version": 1,
        "generated_at": now,
        "snapshot_generated_at": context["generated_at"],
        "resumed_due_ids": due_ids,
        "allocation": {
            "server": "server-6",
            "gpu": 7,
            "max_tasks_per_gpu": 2,
            "gpu_memory_total_mib": 81559,
            "gpu_memory_used_mib": 42023,
            "foreign_process_pid": 3694608,
            "foreign_process_memory_mib": 41996,
            "foreign_process_untouched": True,
        },
        "runtime_observation": {
            "python": "3.10.20",
            "soabi": "cpython-310-x86_64-linux-gnu",
            "torch": "2.8.0+cu128",
            "cuda": "12.8",
            "visible_devices": ["7"],
            "direct_package_count": 9,
            "bootstrap_count": 2,
            "declared_library_count": 8,
            "provenance_receipt_validated": True,
            "abi_compatibility_checked": False,
            "runtime_loader_resolution_verified": False,
        },
        "native_operator_smoke": {
            "extension_imported": True,
            "coordinates_device": "cpu",
            "feature_device": "cuda",
            "forward_succeeded": True,
            "backward_succeeded": True,
            "grad_finite": True,
            "grad_abs_sum": 10.333333969116211,
            "max_allocated_mb": 0.004,
            "full_model_native_backward_verified": False,
            "finding": (
                "voxelization_idx requires CPU coordinate storage; passing "
                "CUDA coordinates segfaults before returning, consistent with "
                "host dereference of a device pointer."),
        },
        "m197_checkpoint": {
            "terminal_state": "stopped_unknown",
            "best_epoch": 23,
            "last_epoch": 26,
            "last_logged_epoch": 27,
            "last_logged_step": 3240,
            "last_logged_total_steps": 4686,
            "optimizer_state_present": True,
            "scheduler_state_present": True,
            "best_miou_observed": 0.49241167306900024,
            "restart_authorized": False,
        },
        "validation": {
            "tests_run": result.testsRun,
            "tests_passed": result.testsRun - len(result.skipped),
            "tests_skipped": len(result.skipped),
            "modules": modules,
            "output": stream.getvalue(),
        },
        "completed_work": [
            "Materialized the dependency collection plan in the server-6 target interpreter.",
            "Collected and validated server-6 dependency provenance without model-package imports.",
            "Fixed the ELF section-header parser and tightened its exact-size fixture.",
            "Verified pointgroup_ops import and a tiny CUDA forward/backward operator path.",
            "Inspected M197 best/last checkpoints, optimizer state, scheduler state and epochs.",
            "Preserved the foreign GPU7 process and avoided queue, launch or checkpoint mutation.",
        ],
        "native_execution_completed": True,
        "operator_native_backward_verified": True,
        "model_native_backward_verified": False,
        "scientific_validation_complete": False,
        "resources_verified": False,
        "admission": False,
        "training_launch": False,
        "checkpoint_transfer": False,
        "queue_changed": False,
        "queue_sha256": queue_hash,
        "next_action": NEXT_ACTION,
        "limitations": [
            "The dependency receipt records observed files and ELF declarations, not loaded bytes.",
            "The operator smoke covers one tiny path and is not model-level validation.",
            "M197 remains stopped_unknown and restart is not authorized.",
            "The three artifact and six data hashes remain to be verified.",
            "The foreign GPU7 process reduces available memory; no eviction was attempted.",
        ],
        "evidence": evidence,
    }
    report_hash = write_new(REPORT, report)
    report_entry = {"path": REPORT, "sha256": report_hash}

    work = read_json(ROOT / "pipeline/research_work.json")
    by_id = {row["id"]: row for row in work["candidates"]}
    for candidate_id in due_ids:
        candidate = by_id[candidate_id]
        merged = {
            item["path"]: item for item in candidate.get("evidence", [])
        }
        merged.update({
            item["path"]: item for item in evidence + [report_entry]
        })
        candidate["stage"] = "diagnosis"
        candidate["latest_progress"] = LATEST
        candidate["next_action"] = NEXT_ACTION
        candidate["evidence"] = list(merged.values())
        candidate.pop("blocker", None)
        candidate.pop("retry_after", None)
        candidate.pop("unblock_condition", None)
        candidate["server6_runtime_progress"] = {
            "timestamp": now,
            "report": REPORT,
            "report_sha256": report_hash,
            "tests_passed": report["validation"]["tests_passed"],
            "tests_skipped": report["validation"]["tests_skipped"],
            "host_observed": True,
            "dependency_provenance_validated": True,
            "operator_native_backward_verified": True,
            "model_native_backward_verified": False,
            "resources_verified": False,
            "admission": False,
        }
    work["last_event_tick"] = {
        "timestamp": now,
        "mode": "event",
        "due_ids": due_ids,
        "evidence": [report_entry],
        "next_action": NEXT_ACTION,
        "result": (
            "Server-6 runtime provenance and a tiny native operator backward "
            "passed; M197 metadata is preserved and queue remains unchanged."),
    }
    if (sha256(ROOT / "pipeline/queue.json") != queue_hash
            or sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    replace_json("pipeline/research_work.json", work)
    print(REPORT)


if __name__ == "__main__":
    main()
