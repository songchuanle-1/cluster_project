"""Persist shared deployment/metadata evidence without granting scientific gates."""
from datetime import datetime
import io
import json
import os
from pathlib import Path
import unittest

from frozen_capture_contract_20260916 import file_sha256


ROOT = Path(__file__).resolve().parents[1]
REPORT = "pipeline/reports/diagnostic_staging_progress_20260920-0315.json"
DECISION = "pipeline/decisions/20260920-031456_other.md"


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_new(path, value):
    with (ROOT / path).open("x", encoding="ascii") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    context = read("pipeline/headless/.tick_context.json")
    if context["generated_at"] != "2026-09-19T19:07:10.921106+00:00":
        raise ValueError("Unexpected tick snapshot")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    work = read("pipeline/research_work.json")
    prior = read("pipeline/reports/remote_inventory_progress_20260920-0215.json")
    staged = read("pipeline/reports/diagnostic_staging_20260920-0315.json")
    metadata = read("pipeline/reports/staged_native_metadata_20260920-0315.json")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    if queue_hash != prior["queue_sha256"] or queue_hash != staged["queue_sha256"]:
        raise ValueError("Queue changed")
    remote = staged["remote"]
    if not (remote["binding_matches"] and remote["sources_stable"]
            and metadata["sources_stable"] and metadata["annotation_and_cache_stable"]
            and metadata["native_dataset_instantiated"]
            and metadata["metadata_matches_source_plan"]
            and metadata["gpu_initialized"] is False
            and metadata["observed_binding"] == staged["expected_binding"]):
        raise ValueError("Staging or native metadata not verified")
    steps = remote["training"]["steps"]
    if len(steps) < 2 or (steps[0]["phase"], steps[0]["step"]) == (
            steps[-1]["phase"], steps[-1]["step"]):
        raise ValueError("Missing native training progress")
    modules = ["test_stage_registry_diagnostic_20260920"] + prior["validation"]["modules"]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Static regression failed")
    now = datetime.now().astimezone().isoformat()
    retry = "2026-09-20T04:07:00+08:00"
    blocker = (
        "GPU7 still at two processes: M197 PID1134192 19956MiB and foreign3827570 "
        "42488MiB; free18597MiB at remote UTC2026-09-19T19:14:33. "
        "Immutable diagnostic sources/registry staged and actual native TRAIN metadata "
        "31/31 verified CPU-only; deployment gap resolved. Zero physical captures. "
        "Independent objectness and candidate-specific scientific gates remain unresolved.")
    next_action = (
        "Reuse immutable bundle /data3/songcl/Project/Cluster_project/pipeline/"
        "diagnostic_bundles/registry_geometry_20260920_0315_88b51c997a74; do not "
        "restage/overwrite it or run destructive legacy sync.sh. Rehash its15 files, "
        "manifest, native dataset/model/config, annotation/cache and M95 archive "
        "pipeline/scm_admission_20260914/best.pth against observed binding before "
        "writing a new expected-binding artifact. Filesystem hardlink/no-overwrite/"
        "directory-fsync and real TRAIN constructor metadata31/31 are verified. "
        "Continue CPU-only physical item/axis preparation on authorized server6 "
        "using dedicated scratch and no training/model/data writes while GPU capped; "
        "metadata alone is not physical join. After " + retry + " query GPU7 once; "
        "only a coordinated free slot and measured memory authorize1-2 original "
        "group forwards via the existing bounded diagnostic runner. No training "
        "launch except admission receipts and safe monitor dispatcher. Verify native "
        "dtype/layout, criterion loss and complete output bundle; retain31-pair "
        "denominators. New TRAIN transforms are not historical replicas. Resolve "
        "independent objectness and each candidate's scientific gates separately; "
        "shared diagnostic progress grants no efficacy, novelty or admission.")
    paths = [
        "scripts/stage_registry_diagnostic_20260920.py",
        "scripts/test_stage_registry_diagnostic_20260920.py",
        "scripts/probe_staged_metadata_20260920.py",
        "scripts/persist_diagnostic_staging_20260920.py",
        "pipeline/reports/diagnostic_staging_20260920-0315.json",
        "pipeline/reports/staged_native_metadata_20260920-0315.json",
        "pipeline/diagnostic_bundles/registry_geometry_20260920_0315_88b51c997a74/manifest.json",
        DECISION]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    passed = result.testsRun - len(result.skipped)
    progress = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        validation=dict(tests_run=result.testsRun, tests_passed=passed,
                        skipped=[dict(test=str(t), reason=r) for t, r in result.skipped],
                        modules=modules, output=stream.getvalue()),
        remote_bundle=remote["bundle"], staged_producer_files=14, staged_registries=1,
        observed_binding=metadata["observed_binding"],
        filesystem=remote["filesystem"],
        native_dataset_instantiated=True, metadata_planned_pairs=31,
        metadata_group_count=len({r["dataset_index"] for r in metadata["native_metadata_plan"]["rows"]}),
        metadata_scene_count=len({r["scene"] for r in metadata["native_metadata_plan"]["rows"]}),
        native_capture_completed=False, captured_pairs=0, missing_binding_pairs=31,
        physical_bindings_verified=0, scientific_validation_complete=False,
        independent_objectness_resolved=False,
        gpu=remote["gpu"], gpu_processes=remote["gpu_processes"], gpu_query_count=1,
        training_progress=dict(first=steps[0], last=steps[-1], previous_tick_max_step=3729),
        queue_sha256=queue_hash, queue_changed=False, training_tree_sync=False,
        diagnostic_staging=True, admission=False, training_launch=False,
        blocker=blocker, retry_after=retry, next_action=next_action,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "First constructor attempt blocked Torch temporary-file writes; raw failure retained.",
            "Retry allowed writes only in fresh dedicated scratch and /dev/null.",
            "One optional uname subprocess denied; dataset constructor still succeeded.",
            "Actual native metadata is not transformed physical support or candidate validation.",
            "No full environment attestation, historical transform replay or GPU reservation.",
            "Legacy sync.sh unsafe operations were read but never executed."])
    write_new(REPORT, progress)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    for candidate in work["candidates"]:
        if candidate["id"] not in context["research_work"]["due_ids"]:
            continue
        evidence_by_path = {e["path"]: e for e in candidate["evidence"]}
        evidence_by_path.update({e["path"]: e for e in evidence + [entry]})
        candidate.update(
            evidence=list(evidence_by_path.values()), blocker=blocker, retry_after=retry,
            next_action=next_action,
            unblock_condition="Independent scientific gates and verified physical capture; "
            "GPU7 below2 processes, measured memory and coordinated execution. "
            "CPU-only original item/axis preparation can proceed while GPU capped.",
            latest_progress=now + ": Immutable14-source+registry bundle staged; actual TRAIN "
            "constructor31/31 metadata verified without CUDA;202 tests,200pass,2skip;0 captures.",
            diagnostic_staging_progress=dict(
                timestamp=now, report=REPORT, report_sha256=entry["sha256"],
                native_dataset_instantiated=True, metadata_planned_pairs=31,
                physical_bindings_verified=0, native_execution_completed=False,
                scientific_validation_complete=False,
                alternatives_attempted="Fixed-byte local tests and immutable remote staging; "
                "hardlink/fsync check; strict read-only constructor attempt then scratch-only "
                "retry; rehash native sources/checkpoint/data; one GPU/log observation."))
    work["last_event_tick"] = dict(timestamp=now, mode="event",
        due_ids=context["research_work"]["due_ids"], evidence=[entry],
        next_action=next_action, result="Diagnostic deployed; native metadata verified; capture pending")
    if file_sha256(ROOT / "pipeline/research_work.json") != work_hash:
        raise ValueError("Concurrent work-state mutation")
    if file_sha256(ROOT / "pipeline/queue.json") != queue_hash:
        raise ValueError("Concurrent queue mutation")
    temporary = "pipeline/research_work.staging.tmp"
    write_new(temporary, work)
    os.replace(ROOT / temporary, ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=entry, passed=passed, skipped=len(result.skipped))))


if __name__ == "__main__":
    main()
