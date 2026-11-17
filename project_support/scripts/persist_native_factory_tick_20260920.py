"""Persist tested factory work without promoting native or scientific gates."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256, model_package_sha256
from native_geometry_runtime_20260919 import MODEL_CLASS
from native_registry_geometry_runner_20260920 import runner_manifest
from persist_import_boundary_tick_20260920 import read, write_new
from relocated_producer_closure_20260920 import ENTRIES, producer_closure
from saved_replay_migration_20260920 import ROOT


REPORT = "pipeline/reports/native_factory_progress_20260920-2015.json"
PRIOR = "pipeline/reports/factory_core_progress_20260920-1915.json"
RETRY = "2026-09-20T21:07:00+08:00"
NEXT = (
    "Continue the existing diagnostic: integrate relocated_native_factory with "
    "the pinned same-child bridge in a fresh synthetic child, then wire the scratch "
    "launcher without exposing an unsandboxed native fallback. Complete package/"
    "extension/dynamic-import attestation and hash the real tokenizer/label-map "
    "inventory before native construction. Add separate location-aware prepare_replay. "
    "Retry server-4 once at/after " + RETRY + "; verify project_cluster interpreter, "
    "bwrap hash/features/kernel, code/data/work paths and GPU0/1 occupancy before "
    "transfer/native work. Verify3 saved artifacts/6 data hashes plus constructor "
    "assets; collate exact3040/3893, then export3921/4278 retaining full31. Real "
    "same-child filesystem probe must precede imports; forwards need coordinated "
    "GPU capacity. No source/local native work or server-6 restart.")
BLOCKER = (
    "Scheduled server-4 SSH attempt refused port22. Runtime/data/GPU, destination "
    "checkpoint bytes and Linux isolation remain unverified. Native factory wrapper "
    "has synthetic constructor tests only; full dependency attestation, launcher "
    "integration and relocated replay remain incomplete.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if context["mode"] != "event" or context["generated_at"] != "2026-09-20T12:07:09.207021+00:00":
        raise ValueError("Wrong tick")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Current decision required")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_relocated_native_factory_20260920"] + read(PRIOR)["validation"]["modules"]
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not tests.wasSuccessful():
        raise ValueError("Regression failed")
    contract = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for row in read(contract)["evidence"]:
        if file_sha256(ROOT / row["path"]) != row["sha256"]:
            raise ValueError("Original migration evidence changed")
    binding = read("pipeline/reports/recovery_physical_20260920-0915.json")["observed_binding"]
    code = ROOT / "Cluster"
    observed = dict(
        producer_sha256=runner_manifest()["producer_sha256"],
        model_source_sha256=model_package_sha256(code, MODEL_CLASS),
        config_sha256=file_sha256(code / "configs/Quard/ctf_hcg_csort" / (MODEL_CLASS + ".yaml")),
        dataset_source_sha256=file_sha256(code / "framework/dataset/scannetv2.py"))
    if any(binding[k] != value for k, value in observed.items()):
        raise ValueError("Original local source binding changed")
    paths = [
        PRIOR, contract, args.decision, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/relocated_native_factory_20260920.py",
        "scripts/test_relocated_native_factory_20260920.py",
        "scripts/persist_native_factory_tick_20260920.py",
        "Cluster/framework/__init__.py", "Cluster/framework/dataset/__init__.py",
        "Cluster/framework/dataset/scannetv2.py"]
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
            tests_run=tests.testsRun, tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            modules=modules, new_tests=18, output=stream.getvalue(),
            native_dependencies_mocked=True, native_data_loaded=False),
        local_original_source_bindings=observed,
        static_producer_closure=producer_closure(
            entries=(*ENTRIES, "relocated_native_factory_20260920.py")),
        completed_work=[
            "Zero-argument build_inputs accepts only an active pinned loader/request.",
            "Constructor verifies documents, three dataset entry sources and saved "
            "location binding before native imports; input files rechecked afterwards.",
            "Label map, annotations, existing graph cache and complete local tokenizer "
            "file inventory required; missing/drifting inputs fail closed.",
            "Deep-copy original TRAIN config, override only data_root, construct dataset "
            "and call existing assemble_inputs without sampling/model loading.",
            "Focused synthetic failure tests and full bounded regression passed."],
        registry_denominator=31, physical_bindings_verified=9,
        physical_bindings_missing=22, model_geometry_captures=0,
        native_factory_wrapper_implemented=True,
        full_native_dependency_closure=False, native_cli_completed=False,
        scratch_write_enforcement_verified=False, native_collation_completed=False,
        relocated_replay_completed=False, destination_bytes_verified=False,
        native_cpu_execution=False, native_gpu_execution=False,
        checkpoint_transfer=False, training_tree_sync=False, training_launch=False,
        admission=False, scientific_validation_complete=False, queue_changed=False,
        queue_sha256=queue_hash, blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "New constructor tests mock native packages, location verifier and assembly; "
            "their underlying contracts have separate prior tests.",
            "Wrapper has not yet run in the pinned same-child bridge.",
            "Real tokenizer/label-map hashes and external package/extension inventories "
            "are unavailable until the authorized host is reachable.",
            "Static file closure is not runtime dependency attestation or authorization.",
            "No native forward/backward, resource, efficacy or checkpoint recovery evidence."])
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
            unblock_condition="Verified server-4 runtime/data/GPU/bwrap, real asset "
                "hashes and external dependency attestation, same-child integration "
                "and native collation. M197 separately requires checkpoint compatibility.")
        candidate["native_factory_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(tests.skipped),
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; saved-only native factory implementation, "
                "constructor asset audit and18 new synthetic tests; original sources rehashed.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/GPU0/1 "
                "before read-only M197 last.pth retrieval; validate optimizer/epoch/path "
                "compatibility before safe resume admission. Preserve stopped_unknown; "
                "no server-6 restart. Shared factory work is not checkpoint recovery.")
            candidate["latest_progress"] = now + ": SSH refused; checkpoint recovery blocked."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = (
                now + ": Native factory wrapper tested synthetically; physical9/model0 unchanged.")
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Missing due record")
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(found), evidence=[entry],
        next_action=NEXT, result="Native factory wrapper tested; native access blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temporary = "pipeline/research_work.native_factory_2015.tmp"
    write_new(temporary, work)
    os.replace(ROOT / temporary, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
