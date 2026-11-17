"""Persist native input readiness without promoting any scientific gate."""
from datetime import datetime
import io
import json
import os
from pathlib import Path
import unittest

from frozen_capture_contract_20260916 import file_sha256


ROOT = Path(__file__).resolve().parents[1]
REPORT = "pipeline/reports/physical_items_progress_20260920-0415.json"
DECISION = "pipeline/decisions/20260920-041435_other.md"
NEXT = (
    "Reuse unchanged immutable registry_geometry_20260920_0315_88b51c997a74 bundle. "
    "First rehash the three saved artifacts in sibling "
    "registry_geometry_20260920_0315_88b51c997a74_physical_20260920_0415_retry "
    "against physical_items_20260920-0415-retry.json. On authorized server-6 CPU, "
    "round-trip trusted item_1097.pth and item_1524.pth, verify complete item/axis "
    "fingerprints and native collation without mutating originals; compare physical "
    "bindings and source/data/archive hashes. These are new TRAIN transforms, not "
    "historical replicas; do not label fresh transforms as these saved captures. "
    "Prepare an explicit exact-item replay adapter only if needed; do not silently "
    "change the immutable runner or overwrite bundle files. After "
    "2026-09-20T05:07:00+08:00 obtain one persisted GPU7 capacity observation; "
    "require coordinated slot and measured memory before 1-2 original-group forwards. "
    "Retain31 registry denominators:3 physical pairs bound,28 missing; model geometry "
    "captures remain0/31. Verify criterion loss, FPS/query identity and complete "
    "geometry output bundle. Independent objectness and each candidate's mechanism, "
    "controls, novelty and admission gates remain separate and unresolved. "
    "No training without receipts plus safe monitor dispatch; never run legacy sync.sh."
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
    if context["generated_at"] != "2026-09-19T20:07:10.954656+00:00":
        raise ValueError("Wrong tick snapshot")
    prior = read("pipeline/reports/diagnostic_staging_progress_20260920-0315.json")
    raw = read("pipeline/reports/physical_items_20260920-0415-retry.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    work = read("pipeline/research_work.json")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    if queue_hash != prior["queue_sha256"]:
        raise ValueError("Queue changed")
    required = ("physical_items_completed", "sources_stable", "annotation_and_cache_stable",
                "manifest_parsed_matches", "manifest_lf_matches")
    if not all(raw.get(k) is True for k in required):
        raise ValueError("Incomplete native item evidence")
    if raw.get("error") or raw["gpu_initialized"] is not False:
        raise ValueError("Native probe failed or violated CPU boundary")
    if raw["binding_counts"] != {"bound": 3, "missing_capture": 28}:
        raise ValueError("Denominator changed")
    if raw["observed_binding"] != prior["observed_binding"]:
        raise ValueError("Native binding changed")
    if [i["dataset_index"] for i in raw["items"]] != [1097, 1524]:
        raise ValueError("Original item selection changed")
    if not all(i["transient_observers_removed"] for i in raw["items"]):
        raise ValueError("Native observer cleanup failed")
    steps = raw["training"]["steps"]
    if not (steps[0]["epoch"] == steps[-1]["epoch"] == 26
            and steps[0]["step"] < steps[-1]["step"]):
        raise ValueError("Training progress missing")
    modules = ["test_probe_physical_items_20260920"] + prior["validation"]["modules"]
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not tests.wasSuccessful():
        raise ValueError("Static regression failed")
    paths = [
        "scripts/probe_physical_items_20260920.py",
        "scripts/test_probe_physical_items_20260920.py",
        "scripts/persist_physical_items_20260920.py",
        "scripts/probe_staged_metadata_20260920.py",
        "pipeline/reports/physical_items_20260920-0415.json",
        "pipeline/reports/physical_items_20260920-0415-retry.json",
        "pipeline/bugfixes/bugfix_20260920-0415.md", DECISION]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    blocker = (
        "Current GPU capacity unverified: first targeted query succeeded but its "
        "output was lost at manifest assertion; no repeat or allocation. Last retained "
        "observation reached two-process cap. Native CPU physical input preparation "
        "now completed for2 groups and3/31 pairs;28 physical joins and all model "
        "geometry captures remain missing. Independent objectness and each "
        "candidate's scientific/admission gates remain unresolved.")
    progress = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        validation=dict(tests_run=tests.testsRun,
                        tests_passed=tests.testsRun-len(tests.skipped),
                        skipped=[dict(test=str(t), reason=r) for t,r in tests.skipped],
                        modules=modules, output=stream.getvalue()),
        physical_items_completed=True, original_dataset_indices=[1097,1524],
        physical_bindings_verified=3, physical_bindings_missing=28,
        registry_denominator=31, physical_pair_summary=raw["physical_pair_summary"],
        remote_artifacts=raw["artifacts"], observed_binding=raw["observed_binding"],
        native_geometry_capture_completed=False, model_forward_completed=False,
        scientific_validation_complete=False, independent_objectness_resolved=False,
        native_gpu_initialized=False, gpu_queries_this_tick=1,
        gpu_measurements_retained=False, gpu_execution_authorized=False,
        training_progress=dict(first=steps[0],last=steps[-1]),
        queue_sha256=queue_hash, queue_changed=False, admission=False,
        training_launch=False, training_tree_sync=False, immutable_bundle_changed=False,
        blocker=blocker, next_action=NEXT, retry_after="2026-09-20T05:07:00+08:00",
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Saved native CPU inputs are not model-query/FPS geometry captures.",
            "Serialization hash checked, but saved item round-trip/collation not yet tested.",
            "New TRAIN transforms cannot reproduce historical failures by identity.",
            "Raw tensors remain remote; local report records hashes and layouts only.",
            "31 failure-local pairs do not estimate population effects.",
            "Manifest byte hashes differ only by exact CRLF-to-LF conversion.",
            "Optional uname subprocess denied by scratch-only audit; no native model failure.",
            "Remote timestamp and local orchestration clock are not assumed synchronized."])
    write_new(REPORT, progress)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    for candidate in work["candidates"]:
        if candidate["id"] not in context["research_work"]["due_ids"]:
            continue
        merged = {e["path"]:e for e in candidate["evidence"]}
        merged.update({e["path"]:e for e in evidence + [entry]})
        candidate.update(
            evidence=list(merged.values()), blocker=blocker, next_action=NEXT,
            retry_after=progress["retry_after"],
            unblock_condition="Separate candidate scientific gates plus verified native "
            "geometry capture; coordinated GPU7 slot and measured memory. CPU round-trip/"
            "collation is executable now; shared input readiness is not candidate admission.",
            latest_progress=now + ": CPU physical items1097/1524 and3/31 bindings saved; "
            "28 missing; no model forward/CUDA;206 static tests,204pass,2skip.",
            physical_item_progress=dict(
                timestamp=now, report=REPORT, report_sha256=entry["sha256"],
                physical_bindings_verified=3, model_forward_completed=False,
                scientific_validation_complete=False,
                alternatives_attempted="Reused/rehashed immutable bundle; diagnosed "
                "CRLF/LF manifest mismatch; retried in new scratch without GPU query; "
                "native CPU TRAIN transforms and physical observer ran successfully; "
                "saved two tensor bundles, full bindings and real layouts; verified "
                "native training steps and source/data stability."))
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=context["research_work"]["due_ids"],
        evidence=[entry], next_action=NEXT,
        result="Three physical pair bindings prepared; GPU forward and science pending")
    if file_sha256(ROOT / "pipeline/research_work.json") != work_hash:
        raise ValueError("Concurrent work mutation")
    if file_sha256(ROOT / "pipeline/queue.json") != queue_hash:
        raise ValueError("Concurrent queue mutation")
    temp = "pipeline/research_work.physical_items.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=entry, tests=tests.testsRun, skipped=len(tests.skipped))))


if __name__ == "__main__":
    main()
