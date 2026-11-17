"""Persist bounded synthetic integration evidence; never promote native gates."""
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


REPORT = "pipeline/reports/factory_bridge_progress_20260920-2115.json"
PRIOR = "pipeline/reports/native_factory_progress_20260920-2015.json"
DECISION = "pipeline/decisions/20260920-211508_other.md"
RETRY = "2026-09-20T22:07:00+08:00"
NEXT = (
    "Continue existing saved-only diagnostic: connect scratch launcher to the tested "
    "pinned same-child factory without an unsandboxed native fallback; complete "
    "external package/extension/dynamic-import attestation and real tokenizer/"
    "label-map hashes. Add separate location-aware prepare_replay. Retry server-4 "
    "once at/after " + RETRY + "; verify project_cluster executable, bwrap hash/"
    "features/kernel, code/data/work paths and GPU0/1 occupancy before transfer/"
    "native work. Verify3 saved artifacts/6 data hashes and constructor assets; "
    "collate exact3040/3893, then export3921/4278 retaining full31. Never regenerate "
    "saved groups. Real same-child filesystem probe precedes native imports; GPU "
    "forwards require coordinated capacity. No source/local native execution.")
BLOCKER = (
    "One scheduled server-4 SSH attempt refused port22. Runtime/GPU, destination "
    "bytes and Linux isolation remain unverified. Factory/bridge integration now "
    "tested in fresh synthetic children, but native dependencies/location/assembly "
    "and successful filesystem probe were mocked. Launcher, external dependency "
    "attestation and relocated replay remain incomplete.")


def main():
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T13:07:07.659687+00:00"):
        raise ValueError("Wrong tick")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_native_factory_bridge_20260920"] + read(PRIOR)["validation"]["modules"]
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not tests.wasSuccessful():
        raise ValueError("Bounded regression failed")
    migration = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for row in read(migration)["evidence"]:
        if file_sha256(ROOT / row["path"]) != row["sha256"]:
            raise ValueError("Original migration evidence drift")
    paths = [
        PRIOR, DECISION, migration, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/test_native_factory_bridge_20260920.py",
        "scripts/persist_factory_bridge_tick_20260920.py",
        "scripts/relocated_native_factory_20260920.py",
        "scripts/same_child_collation_20260920.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=1,
            command="ssh -o BatchMode=yes -o ConnectTimeout=10 -o ConnectionAttempts=1 songcl@192.168.1.137 hostname",
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            evidence_basis="Observed exec_command this tick, not a scripted retry",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(
            tests_run=tests.testsRun, tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(test), reason=reason) for test, reason in tests.skipped],
            modules=modules, new_tests=11, output=stream.getvalue(),
            actual_isolated_synthetic_children=True, native_dependencies_mocked=True,
            location_and_assembly_mocked=True, successful_filesystem_probe_mocked=True,
            native_data_loaded=False),
        completed_work=[
            "Real pinned build_inputs entrypoint integrated with same-child bridge.",
            "Real request, document, dataset-source and constructor-asset checks.",
            "Real native_callbacks, NativeBatchValidator and run_collation on synthetic data.",
            "Same PID confirms probe before factory import, constructor before collation.",
            "Missing/tampered request, source/asset drift, optional tokenizer inventory, "
            "location/constructor/validator/probe failures tested.",
            "Late request drift removes success markers; owned modules cleaned.",
            "Original migration evidence rehashed; queue unchanged."],
        registry_denominator=31, physical_bindings_verified=9, physical_bindings_missing=22,
        model_geometry_captures=0, synthetic_factory_bridge_completed=True,
        native_factory_bridge_completed=False, native_cli_completed=False,
        scratch_write_enforcement_verified=False, destination_bytes_verified=False,
        external_dependency_attestation=False, relocated_replay_completed=False,
        native_cpu_execution=False, native_gpu_execution=False, checkpoint_transfer=False,
        training_tree_sync=False, training_launch=False, admission=False,
        scientific_validation_complete=False, queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Synthetic integration is not Linux sandbox or native environment validation.",
            "Native package imports, SavedPhysicalLocation and assemble_inputs are mocked; "
            "their real lower-level contracts have separate regression tests.",
            "Transitive producer dependencies are not all pinned by this synthetic fixture; "
            "full deployment closure remains a separate gate.",
            "No new diagnostic sample, model forward/backward, resource or efficacy evidence.",
            "Shared engineering evidence does not recover M197 checkpoints."])
    write_new(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    work = read("pipeline/research_work.json")
    found = set()
    for candidate in work["candidates"]:
        if candidate["id"] not in context["research_work"]["due_ids"]:
            continue
        found.add(candidate["id"])
        merged = {item["path"]: item for item in candidate["evidence"]}
        merged.update({item["path"]: item for item in evidence + [entry]})
        candidate.update(
            evidence=list(merged.values()), retry_after=RETRY, blocker=BLOCKER,
            unblock_condition="Verified authorized host runtime/GPU/bwrap, destination "
                "bytes and external dependencies, wired launcher and native saved collation. "
                "M197 separately needs checkpoint compatibility and safe resume admission.")
        candidate["factory_bridge_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(tests.skipped),
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; eleven real isolated-child synthetic "
                "factory/bridge tests and full bounded regression; no native data loaded.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/GPU0/1 "
                "before read-only M197 last.pth retrieval; validate optimizer/epoch/path "
                "compatibility before safe resume admission. Preserve stopped_unknown; "
                "no server-6 restart. Shared bridge tests are not checkpoint recovery.")
            candidate["latest_progress"] = now + ": SSH refused; checkpoint recovery blocked."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = (
                now + ": Pinned factory/bridge integrated synthetically; physical9/model0 unchanged.")
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Missing due record")
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(found), evidence=[entry],
        next_action=NEXT, result="Synthetic factory/bridge integration verified; native access blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temporary = "pipeline/research_work.factory_bridge_2115.tmp"
    write_new(temporary, work)
    os.replace(ROOT / temporary, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
