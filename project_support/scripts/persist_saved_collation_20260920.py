"""Record native replay readiness independently of candidate scientific gates."""
from datetime import datetime
import io
import json
import os
from pathlib import Path
import unittest

from frozen_capture_contract_20260916 import file_sha256


ROOT = Path(__file__).resolve().parents[1]
REPORT = "pipeline/reports/saved_collation_progress_20260920-0515.json"
DECISION = "pipeline/decisions/20260920-051224_other.md"
NEXT = (
    "Reuse the unchanged immutable registry_geometry_20260920_0315_88b51c997a74 "
    "producer and verified saved physical items. Implement and statically test a "
    "separate explicit saved-batch replay entry (do not modify the immutable runner): "
    "rehash batch_1097.pth and batch_1524.pth in sibling "
    "registry_geometry_20260920_0315_88b51c997a74_saved_collation_20260920_0515 "
    "against saved_collation_20260920-0515.json, verify complete batch/axis/item "
    "fingerprints, source/data/archive bindings and physical_bindings.json. Pass "
    "exact batches/axes into existing capture_forward, preserving capture identity "
    "and criterion/FPS/query verification; never regenerate TRAIN transforms under "
    "saved identities. CPU adapter checks remain executable while GPU is busy. "
    "After 2026-09-20T06:07:00+08:00 take one persisted GPU7 capacity observation "
    "and obtain coordinated capacity with measured memory before 1-2 saved-group "
    "forwards. Current two-process cap forbids model execution. Preserve31 pairs: "
    "3 physical bindings,28 missing,0 model geometry captures. Missing other physical "
    "joins remain executable CPU work, not an external blocker. Independent "
    "objectness and every candidate's mechanism/controls/novelty/admission gates "
    "remain unresolved. No training without receipts and safe monitor dispatch; "
    "never invoke legacy sync.sh."
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
    if context["generated_at"] != "2026-09-19T21:07:10.558425+00:00":
        raise ValueError("Wrong tick snapshot")
    prior = read("pipeline/reports/physical_items_progress_20260920-0415.json")
    raw = read("pipeline/reports/saved_collation_20260920-0515.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    work = read("pipeline/research_work.json")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    if queue_hash != prior["queue_sha256"]:
        raise ValueError("Queue changed")
    required = ("saved_collation_completed", "saved_artifacts_verified",
                "full_binding_equal", "sources_stable", "annotation_and_cache_stable",
                "metadata_matches_source_plan")
    if not all(raw.get(k) is True for k in required):
        raise ValueError("Incomplete native saved-collation evidence")
    if raw.get("error") or raw["returncode"] != 0 or raw["gpu_initialized"] is not False:
        raise ValueError("Native probe failed or violated CPU boundary")
    if raw["new_train_transforms"] or raw["model_forward_completed"]:
        raise ValueError("Unexpected new transform/model execution")
    if raw["binding_counts"] != {"bound":3, "missing_capture":28}:
        raise ValueError("Physical denominator changed")
    if raw["observed_binding"] != prior["observed_binding"]:
        raise ValueError("Native source binding changed")
    if [i["dataset_index"] for i in raw["items"]] != [1097,1524]:
        raise ValueError("Saved original item selection changed")
    for item in raw["items"]:
        if not all(item.get(k) is True for k in (
                "roundtrip_verified","repeated_collation_identical","inputs_unchanged")):
            raise ValueError("Incomplete item verification")
    steps = raw["capacity"]["training"]["steps"]
    if not (steps[0]["epoch"] == steps[-1]["epoch"] == 26
            and steps[0]["step"] < steps[-1]["step"]):
        raise ValueError("Increasing native training steps missing")
    modules = ["test_probe_saved_collation_20260920"] + prior["validation"]["modules"]
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not tests.wasSuccessful():
        raise ValueError("Static regression failed")
    paths = [
        "scripts/probe_saved_collation_20260920.py",
        "scripts/test_probe_saved_collation_20260920.py",
        "scripts/persist_saved_collation_20260920.py",
        "pipeline/reports/saved_collation_20260920-0515.json", DECISION]
    evidence = [dict(path=p,sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    blocker = (
        "Observed server-6 GPU7 at two-process cap: M197 PID1134192 plus foreign "
        "PID3827570;18597MiB free does not create a task slot. Native geometry "
        "forward requires coordinated capacity. Exact saved input round-trip, native "
        "collation and full binding reconstruction succeeded on CPU for2 groups; "
        "separate replay entry and28 further physical joins remain executable work. "
        "Independent objectness and candidate-specific scientific/admission gates "
        "are unresolved; shared input readiness does not resolve them.")
    progress = dict(
        schema_version=1,generated_at=now,snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"],evidence=evidence,
        validation=dict(tests_run=tests.testsRun,
                        tests_passed=tests.testsRun-len(tests.skipped),
                        skipped=[dict(test=str(t),reason=r) for t,r in tests.skipped],
                        modules=modules,output=stream.getvalue()),
        saved_collation_completed=True,original_dataset_indices=[1097,1524],
        physical_bindings_verified=3,physical_bindings_missing=28,
        registry_denominator=31,model_geometry_captures=0,
        full_binding_equal=True,full_binding_sha256=raw["full_binding_sha256"],
        remote_artifacts=raw["artifacts"],observed_binding=raw["observed_binding"],
        item_fingerprints=[{k:v for k,v in i.items() if k != "fields"}
                           for i in raw["items"]],
        capacity={k:v for k,v in raw["capacity"].items() if k != "training"},
        training_progress=dict(first=steps[0],last=steps[-1]),
        gpu_queries_this_tick=1,gpu_measurements_retained=True,
        gpu_execution_authorized=False,native_gpu_initialized=False,
        model_forward_completed=False,scientific_validation_complete=False,
        independent_objectness_resolved=False,new_train_transforms=False,
        queue_sha256=queue_hash,queue_changed=False,admission=False,
        training_launch=False,training_tree_sync=False,immutable_bundle_changed=False,
        blocker=blocker,next_action=NEXT,retry_after="2026-09-20T06:07:00+08:00",
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Exact saved inputs and collation do not certify model-internal query/FPS draws.",
            "Three physical bindings are not model geometry captures or efficacy evidence.",
            "31 failure-selected pairs do not estimate population effects.",
            "Independent objectness and each candidate scientific gate remain unresolved.",
            "No native criterion loss/backward/resource benchmark in this CPU probe.",
            "Saved inputs are prior-tick TRAIN transforms, not historical replicas.",
            "External dependency attestation incomplete; hashes identify bytes only.",
            "Optional uname process denied by scratch-only guard; no native model failure.",
            "Remote observation and local orchestration timestamps retained independently."])
    write_new(REPORT,progress)
    entry = dict(path=REPORT,sha256=file_sha256(ROOT / REPORT))
    for candidate in work["candidates"]:
        if candidate["id"] not in context["research_work"]["due_ids"]:
            continue
        merged = {e["path"]:e for e in candidate["evidence"]}
        merged.update({e["path"]:e for e in evidence+[entry]})
        candidate.update(
            evidence=list(merged.values()),blocker=blocker,next_action=NEXT,
            retry_after=progress["retry_after"],
            unblock_condition="Candidate-specific scientific gates plus native geometry "
            "evidence; coordinated GPU7 slot and measured memory for model forwards. "
            "Saved-batch replay integration and remaining physical joins executable "
            "on CPU now; input readiness is not candidate admission.",
            latest_progress=now+": Exact saved inputs1097/1524 round-tripped; repeated "
            "native CPU collation identical and full3/31 physical bindings reconstructed; "
            "2 collated artifacts saved;0 model captures;212 tests,210pass,2skip.",
            saved_collation_progress=dict(
                timestamp=now,report=REPORT,report_sha256=entry["sha256"],
                physical_bindings_verified=3,model_forward_completed=False,
                scientific_validation_complete=False,
                alternatives_attempted="Rehashed saved3 artifacts, immutable producer, "
                "dataset/model/config/archive and source data; CPU serialized exact "
                "items, repeated native collation, compared every physical binding "
                "and saved hashed batches. Persisted one GPU observation and "
                "increasing M197 training steps; no GPU allocation."))
    work["last_event_tick"] = dict(
        timestamp=now,mode="event",due_ids=context["research_work"]["due_ids"],
        evidence=[entry],next_action=NEXT,
        result="Exact native saved-input collation verified; model/science pending")
    if (file_sha256(ROOT / "pipeline/research_work.json") != work_hash
            or file_sha256(ROOT / "pipeline/queue.json") != queue_hash):
        raise ValueError("Concurrent work/queue mutation")
    temp = "pipeline/research_work.saved_collation.tmp"
    write_new(temp,work)
    os.replace(ROOT / temp,ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=entry,tests=tests.testsRun,skipped=len(tests.skipped))))


if __name__ == "__main__":
    main()
