"""Persist executed remote planning evidence without promoting it to capture."""
from datetime import datetime
import io
import json
import os
from pathlib import Path
import unittest

from frozen_capture_contract_20260916 import file_sha256
from remote_registry_inventory_20260920 import training_steps


ROOT = Path(__file__).resolve().parents[1]
REPORT = "pipeline/reports/remote_inventory_progress_20260920-0215.json"
DECISION = "pipeline/decisions/20260920-021557_other.md"


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_new(path, value):
    with (ROOT / path).open("x", encoding="ascii") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    context = read("pipeline/headless/.tick_context.json")
    if context["generated_at"] != "2026-09-19T18:07:11.876295+00:00":
        raise ValueError("Unexpected event snapshot")
    prior = read("pipeline/reports/registry_runner_cli_20260920-0115.json")
    inventory = read("pipeline/reports/remote_registry_inventory_20260920-0215.json")
    checkpoint = read("pipeline/reports/remote_checkpoint_inventory_20260920-0215.json")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    if queue_hash != prior["queue_sha256"]:
        raise ValueError("Queue changed since prior snapshot")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    work = read("pipeline/research_work.json")
    modules = ["test_remote_registry_inventory_20260920"] + prior["validation"]["modules"]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Static validation failed")
    steps = training_steps(inventory["remote"]["training"]["tail"])
    if len(steps) < 2 or steps[-1]["step"] <= steps[0]["step"]:
        raise ValueError("No verified native training progression")
    if not checkpoint["matches"]:
        raise ValueError("Frozen checkpoint mismatch")
    now = datetime.now().astimezone().isoformat()
    retry = "2026-09-20T03:07:00+08:00"
    blocker = (
        "GPU7 at two processes at server UTC2026-09-19T18:16:01: M1971134192 "
        "19956MiB and foreign3827570 42488MiB; free18597MiB. Metadata plans31/31 "
        "resolved but zero physical captures. Checked remote scripts directory lacks "
        "13/14 producer sources and fixed registry is absent at its checked path. "
        "Missing deployment is executable preparation, not a GPU-dependent blocker. "
        "Independent objectness and candidate-specific scientific gates remain unresolved.")
    next_action = (
        "Continue the same diagnostic. Prepare a versioned immutable diagnostic-only "
        "bundle from the existing14-file manifest plus fixed31-pair registry, preserving "
        "every source hash; verify bundle locally, inspect existing sync/closure rules "
        "and stage through the authorized non-destructive diagnostic path without changing "
        "training/model/queue files. Never overwrite existing remote artifacts or bypass "
        "admission for a training launch. Bind the verified M95 archive at "
        "/data3/songcl/Project/Cluster_project/pipeline/scm_admission_20260914/best.pth "
        "(sha256 fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e), "
        "not the absent standard checkpoint directory. Reverify all14 remote sources, "
        "dataset/model/config/checkpoint/registry hashes before creating expected-binding. "
        "Validate actual instantiated scene_inputs against this source-derived plan "
        "without GPU allocation if constructor is confirmed read-only. Check filesystem "
        "hard-link support in a new scratch directory before capture. After " + retry +
        " query GPU7 once; free process slot, measured memory and coordinated execution "
        "are required for1-2 original scene groups. Verify output bundle and native "
        "dtype/layout/progress; retain31 denominators. New transforms are not historical "
        "replicas; no objectness, efficacy or admission claim from metadata/shared tests.")
    paths = [
        "scripts/remote_registry_inventory_20260920.py",
        "scripts/test_remote_registry_inventory_20260920.py",
        "scripts/verify_remote_checkpoint_20260920.py",
        "scripts/persist_remote_inventory_20260920.py",
        "pipeline/reports/remote_registry_inventory_20260920-0215.json",
        "pipeline/reports/remote_checkpoint_inventory_20260920-0215.json", DECISION]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    due = context["research_work"]["due_ids"]
    passed = result.testsRun - len(result.skipped)
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        evidence=evidence, resumed_due_ids=due,
        validation=dict(tests_run=result.testsRun, tests_passed=passed,
                        skipped=[dict(test=str(t), reason=r) for t, r in result.skipped],
                        modules=modules, output=stream.getvalue(),
                        initial_failure="New source-text test used Windows default GBK; corrected to UTF-8."),
        comparisons=inventory["comparisons"],
        metadata_counts=inventory["metadata_plan"]["counts"],
        metadata_scene_count=len({r["scene"] for r in inventory["metadata_plan"]["rows"]}),
        metadata_group_count=len({r["dataset_index"] for r in inventory["metadata_plan"]["rows"]}),
        checkpoint=checkpoint,
        training_progress=dict(first=steps[0], last=steps[-1],
                               previous_tick_max_step=2423, log_verified=True,
                               tail_max_bytes=18000,
                               initial_parser_limitation="Initial probe parser expected bracketed steps; preserved raw tail was reparsed against native tqdm format and tested."),
        gpu=inventory["remote"]["gpu"], gpu_processes=inventory["remote"]["gpu_processes"],
        successful_gpu_query_count=1,
        native_metadata_source_grouping_executed=True,
        native_dataset_instantiated=False, native_execution_completed=False,
        physical_bindings_verified=0, captured_pairs=0, missing_binding_pairs=31,
        scientific_validation_complete=False, independent_objectness_resolved=False,
        blocker=blocker, retry_after=retry, next_action=next_action,
        queue_sha256=queue_hash, queue_changed=False, deployment_performed=False,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=inventory["limitations"])
    write_new(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    for candidate in work["candidates"]:
        if candidate["id"] not in due:
            continue
        by_path = {e["path"]: e for e in candidate["evidence"]}
        by_path.update({e["path"]: e for e in evidence + [entry]})
        candidate.update(
            evidence=list(by_path.values()), blocker=blocker, retry_after=retry,
            next_action=next_action,
            unblock_condition="Scientific gates separately verified; GPU7 below two processes, "
            "sufficient measured memory and coordinated capture. Diagnostic bundle preparation "
            "and metadata checks can proceed while GPU busy.",
            latest_progress=now + ": Remote source-derived TRAIN plan31/31, M95 archive hash "
            "verified;13 remote producer sources missing.194 static tests pass,2 skipped;0 native pairs.",
            remote_inventory_progress=dict(
                timestamp=now, report=REPORT, report_sha256=entry["sha256"],
                metadata_planned_pairs=31, physical_bindings_verified=0,
                native_execution_completed=False, scientific_validation_complete=False,
                alternatives_attempted="Read-only remote source/config/model/annotation inventory; "
                "AST-bounded constructor grouping; explicit archived checkpoint hashing; native "
                "training tail progression; static tests while GPU capped."))
    work["last_event_tick"] = dict(timestamp=now, mode="event", due_ids=due,
                                  evidence=[entry], next_action=next_action,
                                  result="Remote metadata plan complete; native capture not ready")
    if file_sha256(ROOT / "pipeline/research_work.json") != work_hash:
        raise ValueError("Concurrent work-state mutation")
    if file_sha256(ROOT / "pipeline/queue.json") != queue_hash:
        raise ValueError("Concurrent queue mutation")
    write_new("pipeline/research_work.json.tmp", work)
    os.replace(ROOT / "pipeline/research_work.json.tmp", ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=entry, passed=passed, skipped=len(result.skipped),
                          metadata_group_count=report["metadata_group_count"])))


if __name__ == "__main__":
    main()
