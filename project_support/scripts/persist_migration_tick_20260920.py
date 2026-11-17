"""Persist this event's static evidence without touching queue or native hosts."""
from datetime import datetime
import io
import json
import os
from pathlib import Path
import unittest

from frozen_capture_contract_20260916 import file_sha256
from saved_replay_migration_20260920 import ROOT

REPORT = "pipeline/reports/migration_progress_20260920-1015.json"
CONTRACT = "pipeline/reports/saved_replay_migration_20260920-1015.json"
DECISION = "pipeline/decisions/20260920-101324_route_change.md"
NEXT = (
    "At/after2026-09-20T11:07:00+08:00 retry read-only server-4 SSH once. "
    "No new native CPU/GPU diagnostics on server-6; local static only. "
    "Verify server-4 GPU0/1 occupancy/memory, code root, project_cluster and data paths "
    "before sync, transfer or native execution. Then retrieve saved3040/3893 artifacts "
    "read-only without executing source diagnostics, verify the three destination "
    "artifact sizes/hashes plus six data hashes from saved_replay_migration_20260920-1015.json. "
    "Implement/test a separate location adapter and server-4 capacity guard; legacy "
    "driver hardcodes server-6/GPU7 and is not authorized. Keep original provenance "
    "and immutable producer unchanged. Collate/prepare_replay exact saved3040/3893 "
    "only on verified server-4; retain full31 rows, then export3921/4278 there. "
    "Local next executable work while SSH blocked: synthetic-test the location adapter "
    "against relocation, source drift and full-denominator rejection. "
    "Physical coverage9/31 and model captures0/31 remain unchanged; no admission.")
BLOCKER = (
    "server-4 SSH port22 refused this tick, so authorized native runtime, GPU occupancy "
    "and destination data/checkpoint bytes are unverified. Constraint17 prohibits new "
    "CPU/GPU diagnostics on server-6; local is static/orchestration only. Saved3040/3893 "
    "native collation and further exports are blocked on authorized-host access. "
    "The tested metadata contract is not a completed transfer or native path adapter.")


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
    if context["generated_at"] != "2026-09-20T02:07:07.523322+00:00":
        raise ValueError("Wrong event snapshot")
    prior = read("pipeline/reports/cpu_recovery_progress_20260920-0915.json")
    contract = read(CONTRACT)
    if contract["native_execution_authorized"] or contract["model_geometry_captures"] != 0:
        raise ValueError("Static-only boundary differs")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_saved_replay_migration_20260920"] + prior["validation"]["modules"]
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not tests.wasSuccessful():
        raise ValueError("Regression failed")
    paths = [CONTRACT, DECISION, "scripts/saved_replay_migration_20260920.py",
             "scripts/test_saved_replay_migration_20260920.py",
             "scripts/persist_migration_tick_20260920.py",
             "pipeline/analyses/M197-PIRS_stopped_unknown_20260920-0952.md"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"],
        evidence=evidence, mode="event",
        connectivity=dict(server="server-4", host="192.168.1.137", port=22,
            attempts=1, returncode=1, stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            gpu_occupancy_verified=False, runtime_verified=False),
        validation=dict(tests_run=tests.testsRun,
            tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            modules=modules, output=stream.getvalue(), focused_tests_passed=68),
        completed_work=[
            "Validated actual saved3040/3893 metadata with recorded input report hash.",
            "Implemented/tested separate migration location contract for3 artifacts and6 data checks.",
            "Synthetic destination validator rejects path escape,symlinks,size/hash mismatch.",
            "Verified original binding and full31 denominator preserved; source metadata unmodified.",
            "Resumed all8 due records and replaced stale source-host native actions.",
            "Reused existing M197 interruption analysis; no duplicate terminal analysis."],
        physical_bindings_verified=9, physical_bindings_missing=22,
        registry_denominator=31, model_geometry_captures=0,
        native_cpu_execution=False, native_gpu_execution=False,
        checkpoint_transfer=False, training_tree_sync=False, training_launch=False,
        admission=False, scientific_validation_complete=False,
        queue_changed=False, queue_sha256=queue_hash,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        new_questions=[
            "When will server-4 SSH and authorized native runtime be available?",
            "Can saved bytes/data plus M95 and M197 checkpoints verify on server-4 without provenance changes?"
        ],
        blocker=BLOCKER, next_action=NEXT, retry_after="2026-09-20T11:07:00+08:00",
        limitations=[
            "Local tests are static/synthetic; destination bytes were not inspected.",
            "Contract does not execute transfer, native collation, model, backward or training.",
            "Legacy driver still hardcodes server-6/GPU7; do not execute it unchanged.",
            "9/31 physical union is not0/31 model capture or population evidence.",
            "Native runtime and candidate-specific scientific admission remain incomplete."])
    write_new(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    work = read("pipeline/research_work.json")
    for candidate in work["candidates"]:
        if candidate["id"] not in context["research_work"]["due_ids"]:
            continue
        merged = {row["path"]: row for row in candidate["evidence"]}
        merged.update({row["path"]: row for row in evidence + [entry]})
        candidate["evidence"] = list(merged.values())
        candidate["retry_after"] = report["retry_after"]
        candidate["blocker"] = BLOCKER
        candidate["unblock_condition"] = (
            "server-4 SSH and runtime/GPU0/1/data verified, then exact destination hashes "
            "and separate location adapter verified. M197 also needs checkpoint and resume compatibility.")
        candidate["migration_contract_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=tests.testsRun-len(tests.skipped), tests_skipped=len(tests.skipped),
            physical_bindings_verified=9, native_execution_completed=False,
            scientific_validation_complete=False,
            alternatives_attempted="One SSH retry refused; native execution prohibited on source/local. "
                "Completed metadata contract, strict destination byte verifier and synthetic/static regression.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "No restart on server-6. At/after2026-09-20T11:07:00+08:00 verify server-4 "
                "SSH/GPU0/1/runtime/data. Then retrieve and validate M197 last.pth read-only "
                "with optimizer/epoch/path compatibility before any server-4 resume through "
                "the safe gated dispatch path. Interrupted evidence is not efficacy or novelty.")
            candidate["latest_progress"] = now + ": Server-4 SSH refused; existing terminal analysis retained; no restart/transfer."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = now + ": Tested migration contract; physical9/31,model0/31 unchanged; native continuation blocked."
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=context["research_work"]["due_ids"],
        evidence=[entry], next_action=NEXT,
        result="Static migration contract completed; native work awaits authorized server-4")
    if (file_sha256(ROOT / "pipeline/research_work.json") != work_hash
            or file_sha256(ROOT / "pipeline/queue.json") != queue_hash):
        raise ValueError("Concurrent state mutation")
    temporary = "pipeline/research_work.migration_1015.tmp"
    write_new(temporary, work)
    os.replace(ROOT / temporary, ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=REPORT, tests=tests.testsRun, skipped=len(tests.skipped))))


if __name__ == "__main__":
    main()
