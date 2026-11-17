"""Persist measured synthetic bootstrap progress for the 16:07 event tick."""
import argparse
from datetime import datetime
import io
import json
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


PRIOR = "pipeline/reports/pinned_import_progress_20260920-1515.json"
REPORT = "pipeline/reports/cpu_bootstrap_progress_20260920-1615.json"
RETRY = "2026-09-20T17:07:00+08:00"
NEXT = (
    "Continue the existing server-4 CPU diagnostic entrypoint: implement and test "
    "scratch-only filesystem write enforcement before producer/native imports, "
    "then connect checked_imports to native_callbacks/NativeBatchValidator and "
    "run_collation in a fresh child. Do not duplicate loaders or regenerate saved "
    "groups. Add separate location-aware prepare_replay after collation integration. "
    "Retry server-4 SSH once at/after " + RETRY + "; verify actual interpreter, "
    "interface/user, runtime paths and GPU0/1 occupancy before transfer/native work. "
    "No observed server-4 executable or native preflight PASS exists yet. Retrieve "
    "exact3040/3893 read-only, verify3 artifacts/6 data hashes, collate, then "
    "export3921/4278 retaining full31 denominator. GPU work needs coordinated capacity.")
BLOCKER = (
    "One server-4 SSH attempt refused port22. Native host/runtime/data/GPU and "
    "checkpoint bytes remain unverified; new native source/local work prohibited. "
    "Fresh-child imports and runtime validation have synthetic tests; CLI only "
    "performs read-only preflight. Scratch-write boundary, native collation wiring "
    "and relocated replay remain executable local implementation work.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T08:07:08.059709+00:00"):
        raise ValueError("Wrong tick")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Decision outside current project")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_cpu_diagnostic_bootstrap_20260920"] + read(PRIOR)["validation"]["modules"]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Regression failed")
    contract = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for row in read(contract)["evidence"]:
        if file_sha256(ROOT / row["path"]) != row["sha256"]:
            raise ValueError("Migration source evidence changed")
    paths = [PRIOR, contract, args.decision, "SERVERS.yaml", "pipeline/goal.json",
             "scripts/cpu_diagnostic_bootstrap_20260920.py",
             "scripts/test_cpu_diagnostic_bootstrap_20260920.py",
             "scripts/persist_cpu_bootstrap_tick_20260920.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=1,
            command="ssh -o BatchMode=yes -o ConnectTimeout=10 -o ConnectionAttempts=1 songcl@192.168.1.137 hostname",
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            evidence_basis="Observed exec_command result in this tick; not a scripted re-probe",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(
            tests_run=result.testsRun, tests_passed=result.testsRun-len(result.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in result.skipped],
            new_tests=21, modules=modules, output=stream.getvalue(),
            real_child_process_synthetic_tests=True, local_native_data_loaded=False),
        completed_work=[
            "Fresh isolated -I -B child imports verified synthetic producer bytes.",
            "Reject visible CUDA and preimported native dependencies or producer.",
            "Observed interface/user, conda/executable and path validation implemented.",
            "Mocked CLI restricted to read-only runtime preflight; no import/run action.",
            "Original migration evidence unchanged; no immutable producer edited."],
        registry_denominator=31, physical_bindings_verified=9,
        physical_bindings_missing=22, model_geometry_captures=0,
        native_collation_completed=False, native_cli_completed=False,
        scratch_write_enforcement_completed=False, relocated_replay_completed=False,
        destination_bytes_verified=False, native_cpu_execution=False,
        native_gpu_execution=False, checkpoint_transfer=False, training_tree_sync=False,
        training_launch=False, admission=False, scientific_validation_complete=False,
        queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        open_questions=[
            "server-4 SSH restoration and actual interpreter/path layout",
            "Destination saved bytes and M197 optimizer/epoch recovery compatibility",
            "Verified scratch-only boundary compatible with native dependencies"],
        limitations=[
            "Host checks are operational guards, not cryptographic remote attestation.",
            "No Linux native runtime probe was possible; tests use mocked observations.",
            "Synthetic executable fixture is not an observed server-4 executable.",
            "Path redirects/symlinks fail closed pending exact deployment audit.",
            "checked_imports is not a filesystem sandbox or native authorization.",
            "No native data, forward/backward, efficiency, efficacy or novelty evidence.",
            "Shared diagnostic implementation does not advance M197 checkpoint recovery."])
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
            "Verified server-4 runtime/data/GPU and destination bytes; tested "
            "scratch-only CPU collation CLI and relocated replay; GPU needs "
            "coordinated capacity. M197 separately requires checkpoint/admission.")
        candidate["cpu_bootstrap_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"],
            tests_skipped=len(result.skipped), physical_bindings_verified=9,
            model_geometry_captures=0, native_execution_completed=False,
            scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; actual isolated synthetic child "
                "imports and mocked host/runtime CLI tests; no unauthorized native work.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify destination "
                "runtime/data/GPU0/1 before read-only retrieval of M197 last.pth; "
                "validate checkpoint optimizer/epoch/path compatibility before "
                "safe resume admission. No server-6 restart; preserve stopped_unknown. "
                "Shared bootstrap tests do not establish checkpoint recovery or efficacy.")
            candidate["latest_progress"] = now + ": SSH refused; no checkpoint recovery."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = now + ": Synthetic fresh-child bootstrap tested; physical9/model0 unchanged."
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Missing due record")
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(found), evidence=[entry],
        next_action=NEXT, result="Fresh-child bootstrap tested; native execution remains blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temporary = "pipeline/research_work.cpu_bootstrap_1615.tmp"
    write_new(temporary, work)
    os.replace(ROOT / temporary, ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=REPORT, tests=result.testsRun,
                         passed=report["validation"]["tests_passed"],
                         skipped=len(result.skipped))))


if __name__ == "__main__":
    main()
