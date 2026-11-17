"""Persist bounded factory assembly evidence; preserve every scientific gate."""
import argparse
from datetime import datetime
import io
import json
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from relocated_producer_closure_20260920 import producer_closure
from saved_replay_migration_20260920 import ROOT


REPORT = "pipeline/reports/factory_core_progress_20260920-1915.json"
PRIOR = "pipeline/reports/same_child_progress_20260920-1815.json"
RETRY = "2026-09-20T20:07:00+08:00"
NEXT = (
    "Continue the existing diagnostic: implement the zero-argument pinned factory "
    "wrapper that constructs the relocated native dataset and calls the tested "
    "assemble_inputs. Bind runtime packages, tokenizer/label-map files and dynamic "
    "imports; static producer closure alone is not full native provenance. Connect "
    "the scratch launcher to same-child bridge, then add location-aware prepare_replay. "
    "Native CLI remains preflight-only. Retry server-4 once at/after " + RETRY + "; "
    "verify project_cluster interpreter, bwrap hash/features/kernel, code/data/work "
    "paths and GPU0/1 occupancy before transfer/native work. Verify3 saved artifacts/"
    "6 existing data hashes plus additional native constructor dependencies; collate "
    "exact3040/3893 without resampling, then export3921/4278 retaining full31. "
    "Real same-child filesystem probe must precede imports; GPU forwards require "
    "coordinated capacity. No server-6/local native work.")
BLOCKER = (
    "server-4 SSH port22 refused on the one scheduled retry. Actual runtime/data/"
    "GPU, checkpoint bytes and Linux isolation remain unverified. Factory core and "
    "static local producer closure passed synthetic checks; native construction, "
    "external dependency provenance, launcher integration and replay remain work.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T11:07:07.312864+00:00"):
        raise ValueError("Wrong tick")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_relocated_factory_core_20260920"] + read(PRIOR)["validation"]["modules"]
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(output.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Regression failed")
    contract = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for row in read(contract)["evidence"]:
        if file_sha256(ROOT / row["path"]) != row["sha256"]:
            raise ValueError("Original migration evidence changed")
    closure = producer_closure()
    paths = [
        PRIOR, contract, args.decision, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/relocated_factory_core_20260920.py",
        "scripts/relocated_producer_closure_20260920.py",
        "scripts/test_relocated_factory_core_20260920.py",
        "scripts/persist_factory_core_tick_20260920.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=1,
            command="ssh -o BatchMode=yes -o ConnectTimeout=10 -o ConnectionAttempts=1 songcl@192.168.1.137 hostname",
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            evidence_basis="Observed exec_command this tick; no scripted retry",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(
            tests_run=result.testsRun, tests_passed=result.testsRun-len(result.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in result.skipped],
            new_tests=15, modules=modules, output=output.getvalue(),
            factory_native_objects_mocked=True, native_data_loaded=False),
        static_producer_closure=closure,
        completed_work=[
            "Factory core constructs real BindingExporter from original registry bytes "
            "and native scene_inputs without sampling or collation.",
            "Checks dataset class source identity/hash, relocated TRAIN configuration "
            "and full31 metadata dispositions before tensor loading.",
            "CPU loader restricts exact saved paths, rechecks source/data and metadata.",
            "Static producer closure reuses existing AST traversal and rechecks drift; "
            "original capture producer/provenance remains unchanged.",
            "Synthetic failure tests and full bounded regression passed."],
        registry_denominator=31, physical_bindings_verified=9,
        physical_bindings_missing=22, model_geometry_captures=0,
        factory_core_completed=True, native_factory_completed=False,
        full_native_dependency_closure=False, native_cli_completed=False,
        scratch_write_enforcement_verified=False, native_collation_completed=False,
        relocated_replay_completed=False, destination_bytes_verified=False,
        native_cpu_execution=False, native_gpu_execution=False,
        checkpoint_transfer=False, training_tree_sync=False, training_launch=False,
        admission=False, scientific_validation_complete=False, queue_changed=False,
        queue_sha256=queue_hash, blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Factory core accepts a preconstructed native object; wrapper not implemented.",
            "Location verifier is mocked in new tests; covered separately in prior suite.",
            "Static imports are not external package/dynamic import/runtime attestation.",
            "Dataset constructor also needs label map and tokenizer files beyond six "
            "migration data hashes; native full dependency inventory remains incomplete.",
            "No native execution, model capture, backward/resources or efficacy evidence.",
            "Shared diagnostic work does not recover M197 checkpoint."])
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
        candidate.update(
            evidence=list(merged.values()), retry_after=RETRY, blocker=BLOCKER,
            unblock_condition="Verified server-4 runtime/data/GPU/bwrap and complete "
                "native dependency provenance; real same-child probe and native "
                "collation pass. M197 separately requires checkpoint recovery/admission.")
        candidate["factory_core_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"],
            tests_skipped=len(result.skipped), physical_bindings_verified=9,
            model_geometry_captures=0, native_execution_completed=False,
            scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; implemented and tested real "
                "exporter factory assembly plus static local producer closure; synthetic only.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/"
                "GPU0/1 before read-only M197 last.pth retrieval; validate optimizer/"
                "epoch/path compatibility before safe resume admission. Preserve "
                "stopped_unknown; no server-6 restart. Shared factory work is not "
                "checkpoint recovery or efficacy evidence.")
            candidate["latest_progress"] = now + ": SSH refused; checkpoint recovery blocked."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = (
                now + ": Factory assembly/static dependency closure tested; "
                "native wrapper and external provenance incomplete; physical9/model0 unchanged.")
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Missing due candidate")
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(found), evidence=[entry],
        next_action=NEXT, result="Factory assembly regression passed; native blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temporary = "pipeline/research_work.factory_core_1915.tmp"
    write_new(temporary, work)
    os.replace(ROOT / temporary, ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=REPORT, tests=result.testsRun,
                         passed=report["validation"]["tests_passed"],
                         skipped=len(result.skipped), producer_files=len(closure["files"]))))


if __name__ == "__main__":
    main()
