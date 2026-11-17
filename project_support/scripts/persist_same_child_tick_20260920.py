"""Persist tested same-child integration; no native execution or admission."""
from datetime import datetime
import io
import json
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


PRIOR = "pipeline/reports/scratch_boundary_progress_20260920-1715.json"
REPORT = "pipeline/reports/same_child_progress_20260920-1815.json"
DECISION = "pipeline/decisions/20260920-181242_other.md"
RETRY = "2026-09-20T19:07:00+08:00"
NEXT = (
    "Continue existing diagnostic, not a new variant: implement the pinned real "
    "factory for SavedPhysicalLocation/exporter/native collation using relocated "
    "paths without resampling saved groups, and bind the full producer dependency "
    "closure, not only the three direct entry modules. Add location-aware "
    "prepare_replay with original provenance unchanged. Keep native CLI "
    "preflight-only until launcher-to-bridge integration and factory contracts "
    "are tested. Retry server-4 once at/after " + RETRY + "; verify interpreter, "
    "bwrap hash/features/kernel, code/data paths and GPU0/1 before transfer/native "
    "work. Run real same-child filesystem probe before imports; fail closed. "
    "Verify3 artifacts/6 data hashes, collate exact3040/3893, then export3921/4278 "
    "retaining full31. GPU forwards require coordinated capacity.")
BLOCKER = (
    "server-4 SSH port22 refused on one bounded retry. Destination runtime/data/"
    "GPU/checkpoints and real Linux isolation unverified. Same-child synthetic "
    "integration passed, but native factory, full dependency provenance and "
    "launcher bridge remain local implementation work. Local/source native work "
    "remains prohibited.")


def main():
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T10:07:08.264667+00:00"):
        raise ValueError("Wrong tick")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_same_child_collation_20260920"] + read(PRIOR)["validation"]["modules"]
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(output.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Regression failed")
    contract = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for entry in read(contract)["evidence"]:
        if file_sha256(ROOT / entry["path"]) != entry["sha256"]:
            raise ValueError("Original migration evidence changed")
    paths = [PRIOR, contract, DECISION, "SERVERS.yaml", "pipeline/goal.json",
             "scripts/same_child_collation_20260920.py",
             "scripts/test_same_child_collation_20260920.py",
             "scripts/persist_same_child_tick_20260920.py"]
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
            actual_isolated_synthetic_child=True, successful_filesystem_probe_mocked=True,
            real_linux_boundary_test=False, local_native_data_loaded=False,
            initial_failure="One test expected validator rejection but earlier "
                "FrozenDataset axis guard rejected first; changed synthetic defect "
                "to feature dtype to specifically exercise NativeBatchValidator."),
        completed_work=[
            "Connected same-process probe, pinned imports, native_callbacks, real "
            "NativeBatchValidator and run_collation; generated data/dependency mocks only.",
            "Observed common child PID and probe/import/build/collate ordering.",
            "Real unsandboxed local probe rejected writable sentinel before imports.",
            "Tested failed probe, source drift, factory failures, validator failure, "
            "preimports, CUDA visibility, isolation, output ownership and cleanup.",
            "Late source drift removes inner collation success marker.",
            "Original migration evidence rehashed; immutable producer unchanged."],
        registry_denominator=31, physical_bindings_verified=9,
        physical_bindings_missing=22, model_geometry_captures=0,
        same_child_synthetic_integration_completed=True,
        scratch_write_enforcement_verified=False, native_cli_completed=False,
        native_collation_completed=False, relocated_replay_completed=False,
        destination_bytes_verified=False, native_cpu_execution=False,
        native_gpu_execution=False, checkpoint_transfer=False,
        training_tree_sync=False, training_launch=False, admission=False,
        scientific_validation_complete=False, queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Successful probe mocked; no Linux namespace enforcement demonstrated.",
            "Direct bridge modules are pinned, but transitive native/producer "
            "dependencies still need full deployment manifest closure.",
            "Test factory uses synthetic arrays/pickle, not Torch or ScanRefer data.",
            "Production preflight CLI unchanged; sandbox launcher not yet wired.",
            "No native backward/resources/efficacy or novelty gate passed.",
            "Shared diagnostic work does not recover M197 checkpoint.",
            "Host-readable trusted-producer boundary assumes no hostile host races."])
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
            unblock_condition="Verified server-4 runtime/data/GPU and pinned bwrap; "
                "real same-child probe, pinned full producer factory and native "
                "collation pass. M197 separately needs checkpoint compatibility/admission.")
        candidate["same_child_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"],
            tests_skipped=len(result.skipped), physical_bindings_verified=9,
            model_geometry_captures=0, native_execution_completed=False,
            scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; actual fresh-child synthetic "
                "integration and failure regression; no unauthorized native work.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/"
                "GPU0/1 before read-only M197 last.pth retrieval; validate optimizer/"
                "epoch/path compatibility before safe resume admission. Preserve "
                "stopped_unknown; no server-6 restart. Shared synthetic diagnostic "
                "tests are not checkpoint recovery or efficacy evidence.")
            candidate["latest_progress"] = now + ": SSH refused; no checkpoint recovery."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = (
                now + ": Same-child synthetic probe/import/validator/collation "
                "integration passed; real isolation unverified; physical9/model0 unchanged.")
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Missing due record")
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(found), evidence=[entry],
        next_action=NEXT, result="Same-child synthetic integration passed; native blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temporary = "pipeline/research_work.same_child_1815.tmp"
    write_new(temporary, work)
    os.replace(ROOT / temporary, ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=REPORT, tests=result.testsRun,
                         passed=report["validation"]["tests_passed"],
                         skipped=len(result.skipped))))


if __name__ == "__main__":
    main()
