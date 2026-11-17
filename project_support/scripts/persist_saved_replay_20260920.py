"""Persist executed replay readiness without advancing scientific admission."""
from datetime import datetime
import io
import json
import os
from pathlib import Path
import unittest

from frozen_capture_contract_20260916 import file_sha256


ROOT = Path(__file__).resolve().parents[1]
REPORT = "pipeline/reports/saved_replay_progress_20260920-0615.json"
RAW = "pipeline/reports/saved_replay_20260920-0615.json"
DECISION = "pipeline/decisions/20260920-061552_other.md"
NEXT = (
    "Exact saved-batch adapter is implemented and native CPU verified for1097/1524; "
    "do not reimplement it or regenerate saved TRAIN transforms. Reuse immutable "
    "registry_geometry_20260920_0315_88b51c997a74 and separately hash-bound "
    "saved_geometry_replay_20260920.py. Next execute a bounded CPU physical export "
    "for the next one or two unobserved original indices from native_metadata_plan "
    "in saved_replay_20260920-0615.json (exclude1097/1524), retaining all31 pairs "
    "and saving exact items/axes/bindings into a fresh sibling scratch directory. "
    "Do not mark the28 missing physical joins as external blockers. Also wire a "
    "separate bounded native driver using prepare_replay -> replay_forward -> "
    "existing evaluate and atomic outputs; retain original capture identities, "
    "criterion/FPS/query checks and source/data/archive checks before and after. "
    "After2026-09-20T07:07:00+08:00 take one persisted GPU7 observation; require "
    "coordinated slot and measured memory before1-2 saved-group model forwards. "
    "Current two-process cap blocks GPU execution only. No receipt/queue promotion "
    "until candidate-specific mechanism, controls, novelty, independence, backward "
    "and resource gates pass. Never invoke legacy sync.sh."
)


def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))


def write_new(path,value):
    with (ROOT/path).open("x",encoding="ascii") as stream:
        json.dump(value,stream,indent=2,allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def main():
    context = read("pipeline/headless/.tick_context.json")
    if context["generated_at"] != "2026-09-19T22:07:11.494322+00:00":
        raise ValueError("Wrong tick snapshot")
    raw = read(RAW)
    prior = read("pipeline/reports/saved_collation_progress_20260920-0515.json")
    required = ("saved_replay_verified","native_dataset_instantiated",
                "metadata_matches_source_plan","sources_stable","annotation_and_cache_stable")
    if (not all(raw.get(k) is True for k in required) or raw.get("error")
            or raw["returncode"] != 0 or raw["gpu_initialized"] is not False
            or raw["model_forward_completed"] or raw["new_train_transforms"]):
        raise ValueError("Native verification incomplete or CPU boundary differs")
    if (raw["observed_binding"] != prior["observed_binding"]
            or raw["full_binding_sha256"] != prior["full_binding_sha256"]
            or raw["binding_counts"] != {"bound":3,"missing_capture":28}
            or [x["dataset_index"] for x in raw["prepared"]] != [1097,1524]
            or raw["adapter_sha256"] != raw["local_adapter_sha256"]
            or file_sha256(ROOT/"scripts/saved_geometry_replay_20260920.py")
            != raw["adapter_sha256"]):
        raise ValueError("Input/adapter binding differs")
    steps = raw["capacity"]["training"]["steps"]
    if (not steps or steps[0]["epoch"] != steps[-1]["epoch"]
            or steps[0]["step"] >= steps[-1]["step"]
            or raw["capacity"]["process_cap_reached"] is not True):
        raise ValueError("Expected live progress/capacity evidence differs")
    modules = ["test_saved_geometry_replay_20260920"]+prior["validation"]["modules"]
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not tests.wasSuccessful():
        raise ValueError("Regression failed")
    queue_hash = file_sha256(ROOT/"pipeline/queue.json")
    work_hash = file_sha256(ROOT/"pipeline/research_work.json")
    if queue_hash != prior["queue_sha256"]:
        raise ValueError("Queue changed")
    work = read("pipeline/research_work.json")
    paths = ["scripts/saved_geometry_replay_20260920.py",
             "scripts/probe_saved_replay_20260920.py",
             "scripts/test_saved_geometry_replay_20260920.py",
             "scripts/persist_saved_replay_20260920.py",RAW,DECISION]
    evidence = [dict(path=p,sha256=file_sha256(ROOT/p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    blocker = (
        "GPU7 remains at two-process cap (M1971134192 and foreign3827570), "
        "18597MiB free does not create a slot. Native forward requires coordinated "
        "capacity. Saved-batch adapter and exact two-group CPU verification completed; "
        "28 additional physical joins and bounded model-driver integration remain "
        "executable non-GPU work. Independent objectness and candidate-specific "
        "mechanism/controls/novelty/admission gates remain unresolved.")
    progress = dict(
        schema_version=1,generated_at=now,snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"],evidence=evidence,
        validation=dict(tests_run=tests.testsRun,tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t),reason=r) for t,r in tests.skipped],
            modules=modules,output=stream.getvalue()),
        native_cpu_replay_verified=True,synthetic_forward_integration_verified=True,
        physical_bindings_verified=3,physical_bindings_missing=28,
        registry_denominator=31,model_geometry_captures=0,
        observed_binding=raw["observed_binding"],prepared=raw["prepared"],
        full_binding_sha256=raw["full_binding_sha256"],
        adapter_sha256=raw["adapter_sha256"],remote_scratch=raw["scratch"],
        capacity={k:v for k,v in raw["capacity"].items() if k != "training"},
        training_progress=dict(first=steps[0],last=steps[-1]),gpu_queries_this_tick=1,
        native_gpu_initialized=False,model_forward_completed=False,
        scientific_validation_complete=False,independent_objectness_resolved=False,
        new_train_transforms=False,queue_changed=False,queue_sha256=queue_hash,
        admission=False,training_launch=False,training_tree_sync=False,
        immutable_bundle_changed=False,blocker=blocker,next_action=NEXT,
        retry_after="2026-09-20T07:07:00+08:00",
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Adapter forward integration is synthetic only; native CPU path verified real tensors.",
            "No native model forward, criterion loss, backward or resource benchmark.",
            "Saved original capture identities retained; no historical-input replica claim.",
            "31 failure-selected pairs are not population-effect evidence.",
            "Annotation-assisted geometry is not independent objectness or efficacy.",
            "Candidate-specific scientific gates unchanged; shared readiness is not admission.",
            "Adapter separately hashed; immutable producer remains unchanged.",
            "External dependency attestation incomplete; native driver integration pending.",
            "Optional uname denied by scratch guard; native CPU verification succeeded.",
            "Remote and local clocks retained independently."])
    write_new(REPORT,progress)
    entry = dict(path=REPORT,sha256=file_sha256(ROOT/REPORT))
    for candidate in work["candidates"]:
        if candidate["id"] not in context["research_work"]["due_ids"]:
            continue
        merged = {e["path"]:e for e in candidate["evidence"]}
        merged.update({e["path"]:e for e in evidence+[entry]})
        candidate.update(evidence=list(merged.values()),next_action=NEXT,blocker=blocker,
            retry_after=progress["retry_after"],
            unblock_condition="Coordinated GPU7 slot and measured memory for native forwards; "
                "independent candidate-specific scientific gates. Remaining physical joins "
                "and driver wiring executable on CPU, not external blockers.",
            latest_progress=now+": Saved-batch adapter native CPU verified on exact1097/1524; "
                "3/31 physical bindings,0 model captures;224 tests,222pass,2skip.",
            saved_replay_progress=dict(timestamp=now,report=REPORT,
                report_sha256=entry["sha256"],physical_bindings_verified=3,
                model_forward_completed=False,scientific_validation_complete=False,
                alternatives_attempted="Implemented and tested exact-batch adapter through "
                "synthetic criterion capture; executed native CPU full-byte and field/axis/"
                "physical-binding validation on2 saved groups. One persisted GPU/log "
                "observation verified Train26 steps3842->3897; no GPU allocation."))
    work["last_event_tick"] = dict(timestamp=now,mode="event",
        due_ids=context["research_work"]["due_ids"],evidence=[entry],next_action=NEXT,
        result="Saved replay adapter native CPU verified; native forward/science pending")
    if (file_sha256(ROOT/"pipeline/research_work.json") != work_hash
            or file_sha256(ROOT/"pipeline/queue.json") != queue_hash):
        raise ValueError("Concurrent work/queue mutation")
    temp = "pipeline/research_work.saved_replay.tmp"
    write_new(temp,work)
    os.replace(ROOT/temp,ROOT/"pipeline/research_work.json")
    print(json.dumps(dict(report=entry,tests=tests.testsRun,skipped=len(tests.skipped))))


if __name__ == "__main__":
    main()
