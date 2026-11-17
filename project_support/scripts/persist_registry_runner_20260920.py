"""Persist executed event checks and shared progress without admitting training."""
from datetime import datetime
import io
import json
import os
from pathlib import Path
import unittest

from frozen_capture_contract_20260916 import file_sha256
from native_geometry_runtime_20260919 import source_manifest
from native_registry_geometry_runner_20260920 import runner_manifest
from referent_geometry_registry_20260919 import registry_pairs


ROOT = Path(__file__).resolve().parents[1]
REPORT = "pipeline/reports/registry_runner_20260920-0015.json"
SUMMARY = "pipeline/reports/summary_20260920-0015.md"
DECISION = "pipeline/decisions/20260920-001451_other.md"
REGISTRY = "pipeline/reports/referent_control_pairing_20260918-1812.json"


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_new(path, data):
    with (ROOT / path).open("x", encoding="ascii") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    context = read("pipeline/headless/.tick_context.json")
    if context["generated_at"] != "2026-09-19T16:07:11.212024+00:00":
        raise ValueError("Wrong event snapshot")
    if (ROOT / REPORT).exists() or (ROOT / SUMMARY).exists():
        raise ValueError("Event artifacts already exist")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    work = read("pipeline/research_work.json")
    previous = read("pipeline/reports/registry_binding_20260919-2315.json")
    modules = ["test_native_registry_geometry_runner_20260920"] + previous["validation"]["modules"]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Static tests failed")
    old_manifest = source_manifest()
    if old_manifest != previous["producer_manifest"]:
        raise ValueError("Original runtime manifest changed")
    manifest = runner_manifest()
    pairs = registry_pairs(read(REGISTRY))
    if len(pairs) != 31 or len({pair["scene"] for pair in pairs}) != 17:
        raise ValueError("Fixed registry changed")
    now = datetime.now().astimezone().isoformat()
    retry = "2026-09-20T01:07:00+08:00"
    blocker = (
        "Server UTC2026-09-19T16:13:06 GPU7: M197 PID1134192 19956MiB and "
        "foreign PID3827570 42488MiB; free18597MiB, two-process cap reached. "
        "No native runner execution, actual scene_inputs metadata, verified "
        "physical bindings or geometry pairs. Independent objectness unresolved. "
        "Two synthetic Torch tests skipped because local Torch is absent.")
    next_action = (
        "Continue the same diagnostic using native_registry_geometry_runner_20260920.py; "
        "no new reviews, variants or objectness claims. Before remote execution audit "
        "the runner CLI with mocked native dependencies and failure-artifact cases, "
        "including exact expected-binding loading, partial-output rejection and "
        "post-capture source drift. Preserve original11-file runtime manifest. After "
        + retry + " recheck server-6 GPU7 only. Once fewer than two processes and "
        "enough measured memory permit coordinated execution, verify remote producer/"
        "dataset/model/config/checkpoint/registry hashes, prepare expected binding "
        "from verified evidence, and run one-to-two original scene groups with the "
        "separate runner. Verify increasing outputs and physical dtype/layout, then "
        "evaluate missing/ambiguous metadata and binding denominators across all31 "
        "pairs. Smoke completion is not full coverage; new TRAIN transforms do not "
        "reproduce historical failure inputs. Independent objectness and each "
        "candidate's science/backward/resource/admission gates remain incomplete.")
    paths = [
        "scripts/native_registry_geometry_runner_20260920.py",
        "scripts/test_native_registry_geometry_runner_20260920.py",
        "scripts/persist_registry_runner_20260920.py",
        "scripts/referent_registry_binding_20260919.py",
        "Cluster/framework/dataset/scannetv2.py",
        "Cluster/framework/dataset/__init__.py", REGISTRY, DECISION]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    due = context["research_work"]["due_ids"]
    if set(due) - {candidate["id"] for candidate in work["candidates"]}:
        raise ValueError("Missing due candidate")
    passed = result.testsRun - len(result.skipped)
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        scope="Shared registry-aware native runner implementation; static execution only",
        validation=dict(tests_run=result.testsRun, tests_passed=passed,
                        failures=len(result.failures), errors=len(result.errors),
                        skipped=[dict(test=str(t), reason=r) for t, r in result.skipped],
                        modules=modules, output=stream.getvalue()),
        evidence=evidence, resumed_due_ids=due,
        original_runtime_manifest=old_manifest, original_runtime_manifest_changed=False,
        registry_runner_manifest=manifest,
        fixed_registry=dict(requested=31, scenes=17, verified_native_bindings=0,
                            captured_pairs=0, missing_binding_pairs=31,
                            native_metadata_plan_executed=False),
        gpu_observation=dict(
            observed_at_utc="2026-09-19T16:13:06.025216+00:00",
            raw_server_timestamp="2026/09/19 16:13:06.147",
            server="server-6", gpu=7,
            uuid="GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a",
            total_mib=81559, used_mib=62483, free_mib=18597, utilization_percent=31,
            processes=[dict(pid=1134192, memory_mib=19956, role="M197"),
                       dict(pid=3827570, memory_mib=42488, role="foreign")],
            timestamp_note="Server UTC equals00:13 Shanghai; local clock approximately3min behind.",
            query_count=1),
        training_progress=dict(
            phase="Train", epoch=25, total_steps=4686, steps_observed=list(range(1111, 1116)),
            previous_tick_phase="Val", previous_tick_epoch=24, previous_tick_step=263,
            preflight_best_miou=.4924, preflight_no_improve=1,
            pid_config_log_verified=True,
            log="/data3/songcl/Project/Cluster_project/Cluster/logs/"
                "train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pirs_20260916_122540.log",
            completed_current_epoch_claimed=False),
        findings=[
            "Actual runner consumes dataset.scene_inputs; only synthetic metadata tested here.",
            "Uses original planned dataset indices, full expression groups and exact slots.",
            "Exports physical bindings from FrozenDataset before collation without reindexing.",
            "Ambiguous and missing metadata and unprocessed pairs remain in denominators.",
            "Metadata drift before/during observation and collated input mutation fail closed.",
            "Repeated/failed observations cannot resume within one capture.",
            "Executed synthetic two-item and nonzero-slot integration into existing evaluator.",
            "Expected producer/dataset/model/config/checkpoint/registry hashes required by CLI.",
            "Separate transitive14-file runner manifest; original11-file runtime unchanged.",
        ],
        blocker=blocker, retry_after=retry, next_action=next_action,
        native_execution_completed=False, scientific_validation_complete=False,
        independent_objectness_resolved=False, queue_changed=False,
        queue_sha256=queue_hash, deployment_performed=False, new_candidates=0,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Runner CLI/native dependencies and failure-file handling not executed this tick.",
            "No real dataset metadata, native observations or new mechanism evidence.",
            "New TRAIN transforms cannot establish historical-input comparability.",
            "Two-item smoke is not31-pair coverage or a population-effect estimate.",
            "Hashes attest artifact identity, not execution or scientific validity.",
            "Shared tests do not validate seven mechanisms; blocked stages unchanged.",
        ])
    if len(manifest["sources"]) != 14:
        raise ValueError("Unexpected runner source closure")
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
            unblock_condition="GPU7 fewer than two processes and enough measured memory; "
            "coordinated authorized native execution with verified expected hashes and "
            "physical registry bindings. Candidate-specific scientific gates remain separate.",
            latest_progress=now + ": registry-aware runner; %d static tests passed,%d skipped; "
            "zero verified native pairs." % (passed, len(result.skipped)),
            registry_runner_progress=dict(
                timestamp=now, report=REPORT, report_sha256=entry["sha256"],
                tests_passed=passed, tests_skipped=len(result.skipped),
                native_execution_completed=False, scientific_validation_complete=False,
                alternatives_attempted="Integrated native dataset observer and original-index "
                "bounded capture; tested nonzero slots, two-item limits, ambiguous/missing "
                "denominators, mutation and cleanup on synthetic data while GPU capped. "
                "One read-only GPU query verified increasing M197 Train steps."))
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=due, evidence=[entry],
        next_action=next_action, result="Shared static progress; native/admission gates incomplete")
    if file_sha256(ROOT / "pipeline/queue.json") != queue_hash:
        raise ValueError("Queue changed during tick")
    if file_sha256(ROOT / "pipeline/research_work.json") != work_hash:
        raise ValueError("Concurrent research state change")
    write_new("pipeline/research_work.json.tmp", work)
    os.replace(ROOT / "pipeline/research_work.json.tmp", ROOT / "pipeline/research_work.json")
    summary = f"""# Tick 20260920-0015

## 0 Goal Status
- Event snapshot {context['generated_at']}; resume seven due IDs, no new terminal IDs.
- Completed monitor/goal preflight reused; neither rerun. Phase1 NOT YET.
- Target mIoU>=0.51. Ledger M95=.5020, baseline=.4894; exact previously retained
  champion=.5024607181549072, gap=.0075392818. No new efficacy result.
- All16 constraints/11 bans retained; seed1999, schedule and resource gates unchanged.

## 1 GPU Overview
- Only server-6 GPU7 authorized, two total process slots.
- One live observation, server UTC2026-09-19T16:13:06 (00:13 Shanghai):
  total81559MiB, used62483MiB, free18597MiB, utilization31%.
- M197 PID1134192 uses19956MiB; foreign PID3827570 uses42488MiB.
- Two-process cap blocks native capture. No foreign task touched; no local native run.
- Server/local clocks differ by approximately3min. Capacity check is not reservation.

## 2 Running Experiments
- M197-PIRS only project run. Preflight best=.4924, epoch25/50, no_improve1/10.
- Exact PID/config/fd1 log verified; bounded18000-byte tail normalized carriage returns.
- Train[25/50] steps1111..1115/4686 increase beyond previous Val[24/50]263/363.
- No completed current epoch claimed; existing run and schedule preserved.

## 3 Queue Status
- Capacity2, active1, running1, waiting0, claiming0; candidate budget1.
- Queue SHA256 unchanged: {queue_hash}.
- No admissible new mechanism, enqueue, sync, receipt or deployment.
- Seven due IDs resumed with shared evidence: referent-causality-audit stays
  implementation; modality-identity-preservation, referent-discrimination,
  instance-identity-representation, referent-query-selection,
  input-modality-distinguishability and same-target-description-grounding stay blocked.
- No candidate generated to fill the gap: native diagnosis and scientific gates
  incomplete; banned/failed/tuning-only/renamed/placeholder alternatives excluded.

## 4 This Tick's Actions
- Implemented separate registry_geometry_runner_v1 using actual scene_inputs API,
  FrozenDataset observation before collation, original indices/full expression slots,
  bounded one-to-two groups, explicit expected hashes and unchanged criterion observer.
- Retained missing/ambiguous/unprocessed registry pairs; new TRAIN transforms explicitly
  do not reproduce historical inputs. Failure and mutation paths fail closed.
- Executed {result.testsRun} synthetic/static tests: {passed} PASS, {len(result.skipped)} SKIP,
  zero failures/errors. Skips: local Torch absent. No native model/data tests.
- Added nonzero-slot, two-item, mutation, reuse, hook cleanup and evaluator integration
  checks. CLI native dependencies/failure-file paths remain to be tested.
- Runner source closure14 files; original11-file runtime manifest unchanged.
- Fixed registry31 eligible pairs/17 scenes: zero native bindings/captures,
  all31 missing bindings. No independent-objectness or population-effect claim.
- Report: {REPORT}; durable candidate evidence includes SHA256 hashes and next actions.
- Pending questions from snapshot manifest: none. Existing risks retained in memory.
- Summary retention and closure postflight: checked after artifact persistence.

## 5 Decisions Made
- {DECISION}: separate original-index registry-aware diagnostic integration;
  do not promote synthetic tests, metadata plans or geometry to mechanism validation.
- No new route/review or duplicate candidate. Shared progress does not validate seven ideas.
- Native blocker: two-process GPU cap plus unverified remote binding/capture.
- Retry after{retry}; only fewer than two processes, enough memory and
  coordinated authorization permit bound native execution. No direct training dispatch.
- Next executable CPU/static action: mock runner CLI dependencies and audit partial
  outputs, exact expected-binding loading and post-capture source drift. Then verified
  bounded native capture when available; smoke is not31-pair coverage.
"""
    with (ROOT / SUMMARY).open("x", encoding="ascii") as handle:
        handle.write(summary)
    print(json.dumps(dict(report=entry, summary=SUMMARY, resumed=due, passed=passed)))


if __name__ == "__main__":
    main()
