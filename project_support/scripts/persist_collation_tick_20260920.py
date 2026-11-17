"""Persist current event continuation and real local regression evidence."""
import argparse
from datetime import datetime
import io
import json
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from saved_replay_migration_20260920 import ROOT

PRIOR = "pipeline/reports/location_progress_20260920-1215.json"
REPORT = "pipeline/reports/relocated_collation_progress_20260920-1315.json"
RETRY = "2026-09-20T14:07:00+08:00"
NEXT = (
    "At/after 2026-09-20T14:07:00+08:00 retry server-4 SSH once. Before transfer "
    "or native work verify GPU0/1 occupancy/memory, code root, project_cluster "
    "environment and data paths. Retrieve saved3040/3893 bytes read-only from "
    "server-6, verify all3 destination artifacts and6 data hashes plus immutable "
    "producer/model/checkpoint/dataset binding. Wire existing run_collation to "
    "FrozenDataset.collate_fn, native field/feature validator and torch CPU "
    "save/load in a separate server-4-only entrypoint; enforce scratch-only writes "
    "and no CUDA initialization. Callback pipeline is implemented and synthetic "
    "tested; do not reimplement it or regenerate saved groups. If SSH stays "
    "blocked, next local work is the bounded native field validator/entrypoint "
    "integration with mocked imports and CPU-boundary tests. The original "
    "prepare_replay reads original source paths: add a separate location-aware "
    "replay request adapter without editing immutable provenance before replay. "
    "After exact3040/3893 collation, export3921/4278 retaining all31 registry "
    "rows. GPU forwards require actual coordinated slot, fresh capacity and "
    "verified native source, not a boolean-only capacity predicate. Physical9/31, "
    "model0/31; no admission or training launch.")
BLOCKER = (
    "This tick's single server-4 SSH attempt was refused on port22. Authorized "
    "runtime, data, GPU occupancy, destination artifact bytes and M197 checkpoints "
    "remain unverified. New native work on server-6/local is prohibited. "
    "Relocated collation callback pipeline passed synthetic integration only; "
    "native dataset field validator/CLI, relocated replay and real GPU "
    "coordination remain executable implementation work.")


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_new(path, value):
    with (ROOT / path).open("x", encoding="ascii") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T05:07:08.111460+00:00"):
        raise ValueError("Wrong tick")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Current project decision required")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_relocated_saved_collation_20260920"] + read(PRIOR)["validation"]["modules"]
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromNames(modules)
    tests = unittest.TextTestRunner(stream=stream).run(suite)
    print(stream.getvalue())
    if not tests.wasSuccessful():
        raise ValueError("Regression failed")
    contract = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for entry in read(contract)["evidence"]:
        if file_sha256(ROOT / entry["path"]) != entry["sha256"]:
            raise ValueError("Original migration evidence changed")
    paths = [PRIOR, contract, args.decision,
             "scripts/relocated_saved_collation_20260920.py",
             "scripts/test_relocated_saved_collation_20260920.py",
             "scripts/persist_collation_tick_20260920.py",
             "pipeline/goal.json", "SERVERS.yaml"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=1,
            command="ssh -o BatchMode=yes -o ConnectTimeout=8 -o ConnectionAttempts=1 songcl@192.168.1.137 hostname",
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(
            tests_run=tests.testsRun, tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            new_tests=15, modules=modules, output=stream.getvalue(),
            local_native_data_loaded=False),
        completed_work=[
            "Integrated existing SavedPhysicalLocation with bounded repeat-collation callbacks.",
            "Reused verify_payload for saved index/source, field hashes and expression-axis identity.",
            "Checked CPU-only nested values, input immutability and deterministic repeated collation.",
            "Verified serializer roundtrip, byte hashes and final source/full31 binding before publication.",
            "Completion marker published last; failed writes remove only owned batch outputs.",
            "Tested exact3040/3893 synthetic items and full31 denominator with no resampling.",
            "Rehashed immutable migration evidence and retained existing M197 interruption status."],
        registry_denominator=31, physical_bindings_verified=9, physical_bindings_missing=22,
        model_geometry_captures=0, callback_integration_completed=True,
        native_collation_completed=False, destination_bytes_verified=False,
        native_cpu_execution=False, native_gpu_execution=False,
        checkpoint_transfer=False, training_tree_sync=False, training_launch=False,
        admission=False, scientific_validation_complete=False, queue_changed=False,
        queue_sha256=queue_hash, blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        open_questions=[
            "When will server-4 SSH/native runtime become available?",
            "Will original source, destination data and M197 checkpoint bindings match?",
            "Native field validator, server-4-only entrypoint and relocated replay remain unverified."],
        limitations=[
            "Synthetic lists/dictionaries and pickle stand in for native tensors and torch serialization.",
            "Native collate and field-validator callbacks were mocked, not run on ScanRefer data.",
            "No actual destination data hashes, model forward/backward or resource measurements.",
            "CPU callback guard is not a native scratch sandbox or GPU reservation.",
            "M197 recovery requires a separate checkpoint/optimizer/epoch validation; no efficacy claim."])
    write_new(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    work = read("pipeline/research_work.json")
    found = set()
    for candidate in work["candidates"]:
        if candidate["id"] not in context["research_work"]["due_ids"]:
            continue
        found.add(candidate["id"])
        merged = {e["path"]: e for e in candidate["evidence"]}
        merged.update({e["path"]: e for e in evidence + [entry]})
        candidate["evidence"] = list(merged.values())
        candidate["retry_after"] = RETRY
        candidate["blocker"] = BLOCKER
        candidate["unblock_condition"] = (
            "Verified server-4 SSH/runtime/data/GPU0/1 and frozen destination bytes; "
            "native CPU entrypoint integrated/tested. GPU capture separately requires "
            "coordinated capacity. M197 requires validated checkpoint and safe resume admission.")
        candidate["relocated_collation_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(tests.skipped),
            physical_bindings_verified=9, model_geometry_captures=0,
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; completed synthetic relocated collation "
                "integration, byte-bound output and cleanup regression without unauthorized native work.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "No restart on server-6. At/after2026-09-20T14:07:00+08:00 retry server-4 "
                "SSH, verify GPU0/1/runtime/data. Only then retrieve M197 last.pth read-only "
                "and validate checkpoint, optimizer, epoch and path compatibility before "
                "safe gated server-4 resume. Preserve stopped_unknown; collation tests do "
                "not establish M197 recovery, efficacy or mechanism novelty.")
            candidate["latest_progress"] = now + ": SSH refused; no checkpoint transfer or resume."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = now + ": Relocated collation callback integration tested; native9/31 and model0/31 unchanged."
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Due ID missing")
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(found), evidence=[entry],
        next_action=NEXT, result="Synthetic collation integration completed; native execution blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.collation_1315.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=REPORT, tests=tests.testsRun,
                          passed=report["validation"]["tests_passed"],
                          skipped=len(tests.skipped))))


if __name__ == "__main__":
    main()
