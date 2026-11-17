"""Persist executed static checks, not native scientific validation."""
from datetime import datetime
import io
import json
import os
from pathlib import Path
import unittest

from frozen_capture_contract_20260916 import file_sha256
from native_geometry_runtime_20260919 import source_manifest
from native_registry_geometry_runner_20260920 import runner_manifest


ROOT = Path(__file__).resolve().parents[1]
REPORT = "pipeline/reports/registry_runner_cli_20260920-0115.json"
DECISION = "pipeline/decisions/20260920-011328_other.md"


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_new(path, value):
    with (ROOT / path).open("x", encoding="ascii") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    context = read("pipeline/headless/.tick_context.json")
    if context["generated_at"] != "2026-09-19T17:07:10.851012+00:00":
        raise ValueError("Wrong event snapshot")
    previous = read("pipeline/reports/registry_runner_20260920-0015.json")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    work = read("pipeline/research_work.json")
    modules = ["test_registry_runner_cli_20260920"] + previous["validation"]["modules"]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Static regression suite failed")
    original = source_manifest()
    if original != previous["original_runtime_manifest"]:
        raise ValueError("Original eleven-file runtime changed")
    now = datetime.now().astimezone().isoformat()
    retry = "2026-09-20T02:07:00+08:00"
    blocker = (
        "Server UTC2026-09-19T17:13:49 GPU7 remains at two-process cap: M197 "
        "PID1134192 19956MiB, foreign PID3827570 42488MiB, free18597MiB. "
        "No verified native registry metadata, physical bindings or geometry pairs. "
        "Independent objectness and candidate-specific scientific gates unresolved.")
    next_action = (
        "Continue the same registry diagnostic; CLI mocked integration and partial-output "
        "audit are complete. Prepare a read-only remote producer/dataset/model/config/"
        "checkpoint/registry hash inventory and verify expected-binding against actual "
        "artifacts without allocating GPU memory or claiming native execution. Inspect "
        "actual scene_inputs metadata on the authorized server if available without GPU "
        "use; preserve all31 pair denominators and ambiguous joins. After " + retry +
        " recheck GPU7 only; fewer than two processes and enough measured memory plus "
        "coordinated execution permit one-to-two original scene groups. Use verify_output "
        "to reject missing/partial/failed/drifted bundles, then independently verify native "
        "dtype/layout and increasing output. Check native filesystem hard-link support "
        "before capture. Smoke is not full coverage; new TRAIN transforms are not historical "
        "failure-input replicas. No new reviews, variants, objectness claims or admission "
        "until separate science/backward/resource/independence gates pass.")
    paths = [
        "scripts/native_registry_geometry_runner_20260920.py",
        "scripts/test_registry_runner_cli_20260920.py",
        "scripts/persist_registry_runner_cli_20260920.py",
        "pipeline/bugfixes/bugfix_20260920-0115.md", DECISION]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    due = context["research_work"]["due_ids"]
    if set(due) - {c["id"] for c in work["candidates"]}:
        raise ValueError("Missing due candidate")
    passed = result.testsRun - len(result.skipped)
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        scope="Mocked CLI/static synthetic diagnostic audit; no native execution",
        validation=dict(tests_run=result.testsRun, tests_passed=passed,
                        failures=len(result.failures), errors=len(result.errors),
                        skipped=[dict(test=str(t), reason=r) for t, r in result.skipped],
                        modules=modules, output=stream.getvalue()),
        evidence=evidence, resumed_due_ids=due,
        original_runtime_manifest=original, original_runtime_manifest_changed=False,
        registry_runner_manifest=runner_manifest(),
        gpu_observation=dict(
            observed_at_utc="2026-09-19T17:13:49.862261+00:00",
            server="server-6", gpu=7, total_mib=81559, used_mib=62483,
            free_mib=18597, utilization_percent=100,
            processes=[dict(pid=1134192, memory_mib=19956, role="M197"),
                       dict(pid=3827570, memory_mib=42488, role="foreign")],
            successful_query_count=1,
            failed_attempt="Initial PowerShell quoting/PATH failure before GPU query; retried via stdin with absolute remote python.",
            capacity_reserved=False),
        training_progress=dict(
            pid=1134192, phase="Train", epoch=25, steps_observed=[2421, 2422, 2423],
            total_steps=4686, previous_tick_max_step=1115,
            pid_config_log_verified=True, tail_max_bytes=18000,
            log=previous["training_progress"]["log"],
            preflight_best_miou=.4924, preflight_no_improve=1,
            completed_current_epoch_claimed=False),
        fixed_registry=previous["fixed_registry"],
        findings=[
            "Exact expected-binding file loading and extra/mismatched keys fail closed.",
            "Unauthorized paths, occupied GPU, absent metadata and wrong dataset source reject before capture.",
            "Mocked state loading removes only documented position/token-type keys and stays strict.",
            "Post-capture source drift preserves failure evidence without success marker.",
            "JSON serialization precedes filesystem writes; fsynced bytes publish by no-overwrite hard link.",
            "Verifier rejects missing/failure markers, altered artifacts, duplicate/traversal inventory and extra partial files.",
            "CLI success/failure and disk-publication paths executed only with synthetic native dependencies."],
        blocker=blocker, retry_after=retry, next_action=next_action,
        native_execution_completed=False, scientific_validation_complete=False,
        independent_objectness_resolved=False, queue_changed=False,
        queue_sha256=queue_hash, deployment_performed=False, new_candidates=0,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "No real Torch/model/dataset behavior or native filesystem support validated.",
            "All31 real pairs remain without verified native bindings or captures.",
            "Two Torch tests skipped; mocks and hashes do not establish native truth.",
            "Geometry is annotation-assisted nuisance, not objectness or efficacy.",
            "Atomic publication is not a directory-fsync power-loss guarantee.",
            "Shared correctness work does not validate seven candidate mechanisms."])
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
            unblock_condition="GPU7 below two processes, measured memory sufficient, coordinated "
            "native execution and verified remote expected hashes/physical bindings. Scientific "
            "gates remain independent; CPU metadata/source checks need no free GPU.",
            latest_progress=now + ": CLI/failure-artifact audit; %d static tests passed, "
            "%d skipped; zero native pairs." % (passed, len(result.skipped)),
            registry_runner_cli_progress=dict(
                timestamp=now, report=REPORT, report_sha256=entry["sha256"],
                tests_passed=passed, tests_skipped=len(result.skipped),
                native_execution_completed=False, scientific_validation_complete=False,
                alternatives_attempted="Mocked CLI/native imports, synthetic forward integration, "
                "source drift and persistence faults while GPU capped; one successful live "
                "GPU/log query verified increasing M197 training steps."))
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=due, evidence=[entry],
        next_action=next_action, result="Static audit complete; native and admission incomplete")
    if file_sha256(ROOT / "pipeline/queue.json") != queue_hash:
        raise ValueError("Queue changed")
    if file_sha256(ROOT / "pipeline/research_work.json") != work_hash:
        raise ValueError("Concurrent research state change")
    write_new("pipeline/research_work.json.tmp", work)
    os.replace(ROOT / "pipeline/research_work.json.tmp", ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=entry, resumed=due, passed=passed, skipped=len(result.skipped))))


if __name__ == "__main__":
    main()
