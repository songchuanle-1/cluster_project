"""Persist executed CPU coverage and synthetic driver checks, not admission."""
from datetime import datetime
import io
import json
import os
from pathlib import Path
import unittest

from frozen_capture_contract_20260916 import file_sha256

ROOT = Path(__file__).resolve().parents[1]
RAW = "pipeline/reports/next_physical_20260920-0715.json"
REPORT = "pipeline/reports/next_physical_progress_20260920-0715.json"
DECISION = "pipeline/decisions/20260920-071302_other.md"
NEXT = (
    "Physical exports1097/1524 and2690/3011 are saved in separate hash-bound "
    "siblings; cumulative5/31 unique physical pairs,26 missing,0 model captures. "
    "Do not regenerate saved transforms. Next execute CPU exact saved collation "
    "for2690/3011 using existing collator/exporter, then prepare_replay verification "
    "against that two-item binding manifest. Continue next1-2 unobserved indices "
    "3040/3893 from native_metadata_plan with consumed1097,1524,2690,3011 excluded. "
    "Keep full31 denominator per bundle; cumulative coverage union is not a merged "
    "capture. Separate native_saved_geometry_driver_20260920.py orchestration is "
    "synthetically tested but native CLI unexecuted; stage driver+adapter in fresh "
    "sibling with original14-source bundle first on import path, hash-bound request "
    "and CPU CLI/source preflight before coordinated GPU execution. Reuse original "
    "producer and saved capture identities. After2026-09-20T08:07:00+08:00 persist "
    "one GPU7 observation; native1-2 group forwards require coordinated slot and "
    "measured memory. CPU preparation remains executable. No queue promotion until "
    "candidate-specific mechanism/controls/novelty/independence/backward/resource "
    "gates pass; never legacy sync.sh."
)


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_new(path, value):
    with (ROOT / path).open("x", encoding="ascii") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def main():
    context = read("pipeline/headless/.tick_context.json")
    if context["generated_at"] != "2026-09-19T23:07:11.257383+00:00":
        raise ValueError("Wrong event snapshot")
    raw = read(RAW)
    prior = read("pipeline/reports/saved_replay_progress_20260920-0615.json")
    physical = read("pipeline/reports/physical_items_20260920-0415-retry.json")
    for key in ("physical_items_completed", "sources_stable",
                "annotation_and_cache_stable", "previous_artifacts_stable",
                "metadata_matches_source_plan"):
        if raw.get(key) is not True:
            raise ValueError("Native CPU gate failed: " + key)
    if (raw.get("error") or raw["returncode"] != 0 or raw["gpu_initialized"]
            or raw["model_forward_completed"] or raw["selected_indices"] != [2690, 3011]
            or raw["observed_binding"] != prior["observed_binding"]
            or raw["binding_counts"] != {"bound": 2, "missing_capture": 29}):
        raise ValueError("Physical continuation identity/count differs")
    old_ids = {row["pair_id"] for row in physical["physical_pair_summary"]}
    new_ids = {row["pair_id"] for row in raw["physical_pair_summary"]}
    if old_ids & new_ids or len(old_ids | new_ids) != 5:
        raise ValueError("Cumulative coverage is not a disjoint five-pair union")
    modules = ["test_probe_next_physical_20260920",
               "test_native_saved_geometry_driver_20260920"] + prior["validation"]["modules"]
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not tests.wasSuccessful():
        raise ValueError("Regression failed")
    queue_sha = file_sha256(ROOT / "pipeline/queue.json")
    work_sha = file_sha256(ROOT / "pipeline/research_work.json")
    if queue_sha != prior["queue_sha256"]:
        raise ValueError("Queue changed since prior verified snapshot")
    steps = raw["capacity"]["training"]["steps"]
    if (not steps or steps[0]["epoch"] != steps[-1]["epoch"]
            or steps[0]["phase"] != steps[-1]["phase"]
            or steps[0]["step"] >= steps[-1]["step"]
            or raw["capacity"]["process_cap_reached"] is not True):
        raise ValueError("Live progress/capacity differs")
    paths = [RAW, DECISION, "scripts/probe_next_physical_20260920.py",
             "scripts/test_probe_next_physical_20260920.py",
             "scripts/native_saved_geometry_driver_20260920.py",
             "scripts/test_native_saved_geometry_driver_20260920.py",
             "scripts/persist_next_physical_20260920.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    blocker = (
        "GPU7 remains at two-process cap, M1971134192 plus foreign3827570; "
        "18597MiB free does not authorize a third process. Native model capture "
        "requires coordinated capacity. CPU continuation succeeded;26 remaining "
        "physical joins, new saved collation and native driver preflight remain "
        "executable non-GPU work. Candidate-specific scientific gates unresolved.")
    progress = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        validation=dict(tests_run=tests.testsRun, tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            modules=modules, output=stream.getvalue()),
        native_cpu_physical_export_completed=True,
        synthetic_saved_driver_integration_verified=True, native_driver_cli_executed=False,
        physical_bindings_verified=5, physical_bindings_missing=26,
        new_physical_bindings=2, current_bundle_missing=29,
        registry_denominator=31, model_geometry_captures=0,
        cumulative_pair_ids=sorted(old_ids | new_ids),
        cumulative_dataset_indices=[1097, 1524, 2690, 3011],
        observed_binding=raw["observed_binding"], remote_scratch=raw["scratch"],
        capacity={k: v for k, v in raw["capacity"].items() if k != "training"},
        training_progress=dict(first=steps[0], last=steps[-1]),
        gpu_queries_this_tick=1, native_gpu_initialized=False,
        scientific_validation_complete=False, independent_objectness_resolved=False,
        model_forward_completed=False, queue_changed=False, queue_sha256=queue_sha,
        admission=False, training_launch=False, training_tree_sync=False,
        immutable_bundle_changed=False, blocker=blocker, next_action=NEXT,
        retry_after="2026-09-20T08:07:00+08:00",
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Cumulative5/31 is a disjoint physical-input coverage union, not merged captures.",
            "Current fresh bundle contains2 bound and29 missing; previous bundle3 and28.",
            "Saved new TRAIN transforms are not historical failure-input replicas.",
            "No native model forward, criterion loss, backward or resource measurement.",
            "Driver orchestration tested synthetically; native CLI still unexecuted.",
            "Annotation-assisted geometry is not independent objectness or efficacy.",
            "Seven mechanisms retain separate unresolved scientific admission gates.",
            "Optional uname blocked by scratch guard; native CPU exports succeeded.",
            "Remote and local clocks retained independently."])
    write_new(REPORT, progress)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    work = read("pipeline/research_work.json")
    for candidate in work["candidates"]:
        if candidate["id"] not in context["research_work"]["due_ids"]:
            continue
        merged = {row["path"]: row for row in candidate["evidence"]}
        merged.update({row["path"]: row for row in evidence + [entry]})
        candidate.update(
            evidence=list(merged.values()), next_action=NEXT, blocker=blocker,
            retry_after=progress["retry_after"],
            unblock_condition="Coordinated GPU7 slot and measured memory for native "
                "forwards; independent scientific gates. CPU preparation not blocked.",
            latest_progress=now + ": Exported original2690/3011 on native CPU; "
                "cumulative5/31 physical bindings,0 model captures; driver synthetic tests pass.",
            next_physical_progress=dict(
                timestamp=now, report=REPORT, report_sha256=entry["sha256"],
                physical_bindings_verified=5, model_forward_completed=False,
                scientific_validation_complete=False,
                alternatives_attempted="Native CPU export of two new groups, previous "
                    "artifact rehash and full31 binding manifests; separate saved-driver "
                    "integration and failure tests; one persisted GPU/log observation."))
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=context["research_work"]["due_ids"],
        evidence=[entry], next_action=NEXT,
        result="Two new native CPU groups saved; synthetic replay driver verified")
    if (file_sha256(ROOT / "pipeline/research_work.json") != work_sha
            or file_sha256(ROOT / "pipeline/queue.json") != queue_sha):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.next_physical.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=entry, tests=tests.testsRun, skipped=len(tests.skipped))))


if __name__ == "__main__":
    main()
