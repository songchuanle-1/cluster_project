"""Persist static validation progress without promoting native research gates."""
import argparse
from datetime import datetime
import io
import json
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from saved_replay_migration_20260920 import ROOT

PRIOR = "pipeline/reports/relocated_collation_progress_20260920-1315.json"
REPORT = "pipeline/reports/native_batch_validation_progress_20260920-1418.json"
RETRY = "2026-09-20T15:07:00+08:00"
NEXT = (
    "At/after2026-09-20T15:07:00+08:00 retry server-4 SSH once; verify runtime, "
    "data, code root and GPU0/1 occupancy before transfer/native work. Existing "
    "NativeBatchValidator/native_callbacks now bind FrozenDataset.collate_fn and "
    "CPU serialization; do not recreate wrappers. Next local work: server-4-only "
    "CPU entrypoint with immutable import/source verification, scratch-only write "
    "enforcement and mocked CLI tests. Then implement separate location-aware "
    "prepare_replay without modifying original provenance. Once host verified, "
    "retrieve exact3040/3893 bytes read-only from server-6, verify3 artifacts and6 "
    "data hashes, collate exact inputs, then export3921/4278 with full31 rows. "
    "Never regenerate recovered groups. GPU capture requires real coordinated "
    "capacity, not an observation predicate. Physical9/31 and model0/31 unchanged.")
BLOCKER = (
    "One server-4 SSH attempt refused port22; destination runtime/data/GPU and "
    "checkpoint bytes unverified. No new native work on source/local allowed. "
    "Native field/callback checks passed synthetic tests only. Authorized CPU "
    "entrypoint, immutable import binding, scratch enforcement, relocated replay "
    "and GPU coordination remain executable implementation work.")


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
            or context["generated_at"] != "2026-09-20T06:07:08.033864+00:00"):
        raise ValueError("Wrong tick")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Current decision required")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_native_saved_batch_validation_20260920"] + read(PRIOR)["validation"]["modules"]
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not tests.wasSuccessful():
        raise ValueError("Regression failed")
    contract = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for row in read(contract)["evidence"]:
        if file_sha256(ROOT / row["path"]) != row["sha256"]:
            raise ValueError("Migration evidence changed")
    paths = [PRIOR, contract, args.decision, "pipeline/bugfixes/bugfix_20260920-1415.md",
             "scripts/native_saved_batch_validation_20260920.py",
             "scripts/test_native_saved_batch_validation_20260920.py",
             "scripts/relocated_saved_collation_20260920.py",
             "scripts/persist_batch_validation_tick_20260920.py",
             "pipeline/goal.json", "SERVERS.yaml"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(server="server-4", attempts=1, returncode=1,
            command="ssh -o BatchMode=yes -o ConnectTimeout=8 -o ConnectionAttempts=1 songcl@192.168.1.137 hostname",
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(tests_run=tests.testsRun,
            tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            new_tests=29, modules=modules, output=stream.getvalue(),
            local_native_data_loaded=False),
        completed_work=[
            "Native sixteen-field item, expression axes, counts and passthrough field validation.",
            "Exact feature concatenation including dtype and point/token/mask shape checks.",
            "Bound real FrozenDataset wrapper to supplied native collate and CPU load/save callbacks.",
            "Reject CUDA initialization before/after callbacks; preserve saved nonzero occurrence.",
            "Fixed CPU string-device rejection exposed by synthetic NumPy arrays.",
            "Rehashed immutable migration evidence; source producer and training tree unchanged."],
        registry_denominator=31, physical_bindings_verified=9, physical_bindings_missing=22,
        model_geometry_captures=0, native_collation_completed=False,
        native_cli_completed=False, scratch_write_enforcement_completed=False,
        relocated_replay_completed=False, destination_bytes_verified=False,
        native_cpu_execution=False, native_gpu_execution=False,
        checkpoint_transfer=False, training_tree_sync=False, training_launch=False,
        admission=False, scientific_validation_complete=False,
        queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        open_questions=["server-4 restoration and destination data/source compatibility",
                        "M197 checkpoint/optimizer/epoch recovery compatibility"],
        limitations=[
            "NumPy arrays/mock Torch are synthetic; native dataset and Torch not executed.",
            "Real FrozenDataset wrapper tested with mocked native collate only.",
            "Callback guards are not host authorization or a filesystem sandbox.",
            "Voxel map values/tokenizer semantics still require native verification.",
            "No forward/backward, efficiency, efficacy or novelty evidence.",
            "Shared validation does not advance M197 checkpoint recovery."])
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
            "Verified server-4 runtime/data/source and destination bytes; tested "
            "CPU entrypoint/scratch guard and relocated replay. GPU needs coordinated "
            "slot. M197 separately needs validated checkpoint and safe resume admission.")
        candidate["native_batch_validation_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(tests.skipped),
            physical_bindings_verified=9, model_geometry_captures=0,
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; synthetic native-field and CPU callback "
                "implementation/tests; no unauthorized work.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "At/after2026-09-20T15:07:00+08:00 retry server-4 once. Verify runtime/data/"
                "GPU0/1 before read-only retrieval of M197 last.pth from server-6; validate "
                "checkpoint optimizer/epoch/path compatibility before safe resume admission. "
                "No restart on server-6. Preserve stopped_unknown; shared field tests do "
                "not establish checkpoint recovery, efficacy or mechanism novelty.")
            candidate["latest_progress"] = now + ": SSH refused; no checkpoint transfer/resume."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = now + ": Synthetic native-field/callback checks; physical9/model0 unchanged."
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Missing due record")
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(found), evidence=[entry],
        next_action=NEXT, result="Static field/callback implementation complete; native access blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.batch_validation_1418.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=REPORT, tests=tests.testsRun,
                          passed=report["validation"]["tests_passed"],
                          skipped=len(tests.skipped))))


if __name__ == "__main__":
    main()
