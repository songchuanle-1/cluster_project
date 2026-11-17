"""Persist recovered CPU evidence; never modify queue or scientific stages."""
from datetime import datetime
import io
import json
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from recover_cpu_progress_20260920 import (
    ROOT, REPLAY, PHYSICAL, OUTPUT, read, validate_recovery, write_new)

REPORT = "pipeline/reports/cpu_recovery_progress_20260920-0915.json"
NEXT = (
    "Recovered0815 native CPU collation/replay and driver import/help/uncoordinated "
    "rejection for2690/3011 are verified; do not repeat. New saved CPU groups3040/3893 "
    "in *_physical_20260920_0915 add4 pairs; cumulative9/31 physical coverage,22 "
    "missing,0/31 model captures. Next collate exact saved3040/3893 and prepare_replay "
    "against their full31 binding manifest without regenerating transforms. Reuse "
    "collator/adapter/driver; separate hashed sources, immutable14-source producer "
    "first on import path. Then export next1-2 original indices3921/4278 excluding "
    "1097/1524/2690/3011/3040/3893. Keep31 denominator per bundle; union is not merged "
    "model capture. Staged2690/3011 driver/request already lives in "
    "*_saved_replay_20260920_0815; model allocation path remains unexecuted. "
    "After2026-09-20T10:07:00+08:00 take one GPU7 observation; coordinated free slot "
    "plus measured memory precede1-2 saved-group native forwards. CPU preparation "
    "remains executable. No promotion until candidate-specific mechanism/controls/"
    "novelty/independence/backward/resource gates pass; never legacy sync.sh.")


def main():
    context = read("pipeline/headless/.tick_context.json")
    if context["generated_at"] != "2026-09-20T01:07:11.961854+00:00":
        raise ValueError("Wrong recovery snapshot")
    queue_sha = file_sha256(ROOT / "pipeline/queue.json")
    work_sha = file_sha256(ROOT / "pipeline/research_work.json")
    prior = read("pipeline/reports/next_physical_progress_20260920-0715.json")
    if queue_sha != prior["queue_sha256"]:
        raise ValueError("Queue differs")
    replay, physical, raw = read(REPLAY), read(PHYSICAL), read(OUTPUT)
    validate_recovery(replay, physical)
    for key in ("physical_items_completed", "sources_stable",
                "annotation_and_cache_stable", "previous_artifacts_stable",
                "metadata_matches_source_plan", "recovered_artifacts_verified",
                "recovered_artifacts_stable"):
        if raw.get(key) is not True:
            raise ValueError("Native gate failed: " + key)
    if (raw.get("error") or raw["returncode"] != 0 or raw["gpu_initialized"]
            or raw["model_forward_completed"] or raw["selected_indices"] != [3040, 3893]
            or raw["observed_binding"] != prior["observed_binding"]
            or raw["binding_counts"] != {"bound": 4, "missing_capture": 27}
            or raw["recovered_replay_sha256"] != file_sha256(ROOT / REPLAY)):
        raise ValueError("Capture identity/boundary differs")
    old_ids = set(prior["cumulative_pair_ids"])
    new_ids = {row["pair_id"] for row in raw["physical_pair_summary"]}
    if old_ids & new_ids or len(old_ids | new_ids) != 9:
        raise ValueError("Physical union not nine disjoint pairs")
    steps = raw["capacity"]["training"]["steps"]
    if (not steps or steps[0]["phase"] != "Train" or steps[-1]["phase"] != "Train"
            or steps[0]["epoch"] != steps[-1]["epoch"]
            or steps[0]["step"] >= steps[-1]["step"]
            or raw["capacity"]["process_cap_reached"] is not True):
        raise ValueError("Training/capacity differs")
    modules = ["test_recover_cpu_progress_20260920",
               "test_probe_next_saved_replay_20260920"] + prior["validation"]["modules"]
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not tests.wasSuccessful():
        raise ValueError("Regression failed")
    paths = [REPLAY, OUTPUT,
        "pipeline/decisions/20260920-081349_other.md",
        "pipeline/decisions/20260920-091515_other.md",
        "scripts/probe_next_saved_replay_20260920.py",
        "scripts/test_probe_next_saved_replay_20260920.py",
        "scripts/recover_cpu_progress_20260920.py",
        "scripts/test_recover_cpu_progress_20260920.py",
        "scripts/persist_cpu_recovery_20260920.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    blocker = (
        "GPU7 two-process cap:M1971134192 and foreign3827570;18597MiB free does "
        "not authorize third process. Model execution requires coordinated capacity. "
        "CPU collation3040/3893 and remaining22 physical joins are executable,not "
        "external blockers. Candidate-specific scientific gates unresolved.")
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        recovery=dict(interrupted_tick="20260920-080701",
            failure="Upstream503/auth-unavailable interruption after successful CPU work",
            recovered_replay=REPLAY, saved_transforms_rerun=False,
            recovered_artifacts_rehashed=raw["recovered_artifact_count"]),
        validation=dict(tests_run=tests.testsRun, tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            modules=modules, output=stream.getvalue()),
        native_cpu_physical_export_completed=True, recovered_native_cpu_replay_verified=True,
        native_driver_help_verified=True, native_driver_model_path_executed=False,
        new_physical_bindings=4, physical_bindings_verified=9, physical_bindings_missing=22,
        current_bundle_binding_counts=raw["binding_counts"], registry_denominator=31,
        cumulative_pair_ids=sorted(old_ids | new_ids),
        cumulative_dataset_indices=[1097,1524,2690,3011,3040,3893],
        model_geometry_captures=0, observed_binding=raw["observed_binding"],
        remote_scratch=raw["scratch"], recovered_replay_scratch=replay["scratch"],
        replay_request=replay["replay_request"], separate_sources=replay["separate_sources"],
        capacity={k:v for k,v in raw["capacity"].items() if k != "training"},
        training_progress=dict(first=steps[0], last=steps[-1]),
        gpu_queries_this_tick=1, native_gpu_initialized=False, model_forward_completed=False,
        scientific_validation_complete=False, independent_objectness_resolved=False,
        queue_changed=False, queue_sha256=queue_sha, admission=False,
        training_launch=False, training_tree_sync=False, immutable_bundle_changed=False,
        blocker=blocker, next_action=NEXT, retry_after="2026-09-20T10:07:00+08:00",
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "9/31 physical union is not merged model capture or population evidence.",
            "New bundle4/27; prior bundles3/28 and2/29; all denominator31.",
            "Saved TRAIN transforms are not historical failure replicas.",
            "No native forward,criterion,backward or resource benchmark.",
            "Driver parser/import/guard verified; model path unexecuted.",
            "Geometry is annotation-assisted nuisance, not independent objectness.",
            "Seven hypotheses retain separate scientific gates; no admission.",
            "Optional uname denied by scratch guard; native CPU execution succeeded.",
            "Remote/local clocks retained separately; external attestation incomplete."])
    write_new(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    work = read("pipeline/research_work.json")
    for candidate in work["candidates"]:
        if candidate["id"] not in context["research_work"]["due_ids"]:
            continue
        merged = {row["path"]:row for row in candidate["evidence"]}
        merged.update({row["path"]:row for row in evidence + [entry]})
        candidate.update(
            evidence=list(merged.values()), next_action=NEXT, blocker=blocker,
            retry_after=report["retry_after"],
            unblock_condition="Coordinated GPU7 slot plus measured memory for native "
                "forward; candidate-specific science gates. CPU work executable.",
            latest_progress=now + ": Recovered0815 replay; exported3040/3893 "
                "for cumulative9/31 physical bindings;0 model captures.",
            cpu_recovery_progress=dict(timestamp=now, report=REPORT,
                report_sha256=entry["sha256"], physical_bindings_verified=9,
                model_forward_completed=False, scientific_validation_complete=False,
                alternatives_attempted="Rehashed saved CPU batches,request and driver; "
                    "native CPU exported two groups while GPU capped;241 regression "
                    "tests and one increasing Train27 observation."))
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=context["research_work"]["due_ids"],
        evidence=[entry], next_action=NEXT,
        result="Interrupted replay recovered; four additional physical bindings")
    if (file_sha256(ROOT / "pipeline/research_work.json") != work_sha
            or file_sha256(ROOT / "pipeline/queue.json") != queue_sha):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.cpu_recovery.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=entry, tests=tests.testsRun, skipped=len(tests.skipped))))


if __name__ == "__main__":
    main()
