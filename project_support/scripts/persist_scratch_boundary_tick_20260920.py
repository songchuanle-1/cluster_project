"""Persist the bounded 17:07 scratch-boundary tick without native admission."""
from datetime import datetime
import io
import json
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


PRIOR = "pipeline/reports/cpu_bootstrap_progress_20260920-1615.json"
REPORT = "pipeline/reports/scratch_boundary_progress_20260920-1715.json"
DECISION = "pipeline/decisions/20260920-171200_other.md"
RETRY = "2026-09-20T18:07:00+08:00"
NEXT = (
    "Continue the existing CPU diagnostic entrypoint by connecting the scratch "
    "probe, checked_imports, native_callbacks/NativeBatchValidator and "
    "run_collation in the SAME isolated child, with synthetic integration tests. "
    "Keep the production CLI preflight-only until tested. Add a separate "
    "location-aware prepare_replay without mutating original provenance. "
    "Retry server-4 once at/after " + RETRY + "; independently verify actual "
    "interpreter, bubblewrap binary/hash/features, kernel namespace support, "
    "runtime/data paths and GPU0/1 occupancy before transfer or native work. "
    "Run the real filesystem probe before any producer imports; fail closed, no "
    "unsandboxed fallback. Retrieve exact3040/3893 read-only, verify3 artifacts/"
    "6 data hashes, collate, then export3921/4278 with full31 denominator. "
    "Do not regenerate saved groups. GPU work needs coordinated capacity.")
BLOCKER = (
    "One server-4 SSH retry refused port22; destination runtime, data, GPU and "
    "checkpoint bytes remain unverified. Scratch probe argv and orchestration "
    "have static/mocked tests only; no Linux namespace enforcement was observed. "
    "Native source/local execution remains prohibited. Same-child pinned-import/"
    "collation integration and relocated replay remain local implementation work.")


def main():
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T09:07:08.390417+00:00"):
        raise ValueError("Wrong tick")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_scratch_cpu_boundary_20260920"] + read(PRIOR)["validation"]["modules"]
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
    paths = [
        PRIOR, contract, DECISION, "SERVERS.yaml", "pipeline/goal.json",
        "scripts/scratch_cpu_boundary_20260920.py",
        "scripts/test_scratch_cpu_boundary_20260920.py",
        "scripts/persist_scratch_boundary_tick_20260920.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=1,
            command="ssh -o BatchMode=yes -o ConnectTimeout=10 -o ConnectionAttempts=1 songcl@192.168.1.137 hostname",
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            evidence_basis="Observed exec_command this tick; no scripted re-probe",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(
            tests_run=result.testsRun, tests_passed=result.testsRun-len(result.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in result.skipped],
            new_tests=19, modules=modules, output=output.getvalue(),
            boundary_tests_static_or_mocked=True, real_linux_boundary_test=False,
            local_native_data_loaded=False,
            initial_test_failures="Two Windows short-path fixture failures corrected "
                "by resolving the test temp root; production validation not relaxed."),
        completed_work=[
            "Implemented read-only-root, scratch-output-only Linux probe launcher.",
            "Reject wrong runtime/binary hash before sandbox attempt; no fallback.",
            "Hide GPUs, clear child environment, close inherited file descriptors.",
            "Probe read-only sentinel write opens/mkdir and writable scratch output.",
            "Check receipt and host sentinel/output bytes; keep artifacts on failure.",
            "Upstream source review replaced invalid shm remount with devpts remount.",
            "Original migration evidence rehashed; immutable producer untouched."],
        upstream_review=[
            "https://raw.githubusercontent.com/containers/bubblewrap/main/bwrap.xml",
            "https://raw.githubusercontent.com/containers/bubblewrap/main/bubblewrap.c"],
        registry_denominator=31, physical_bindings_verified=9,
        physical_bindings_missing=22, model_geometry_captures=0,
        boundary_launcher_implemented=True, scratch_write_enforcement_verified=False,
        same_child_native_integration_completed=False, native_cli_completed=False,
        native_collation_completed=False, relocated_replay_completed=False,
        destination_bytes_verified=False, native_cpu_execution=False,
        native_gpu_execution=False, checkpoint_transfer=False, training_tree_sync=False,
        training_launch=False, admission=False, scientific_validation_complete=False,
        queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        open_questions=[
            "server-4 SSH restoration and independently observed interpreter/bwrap",
            "Kernel namespace support and native-dependency compatibility",
            "Destination saved bytes and M197 optimizer/epoch/path compatibility"],
        limitations=[
            "No Linux mounts or kernel enforcement tested locally or remotely.",
            "Mocked launcher success is not observed server-4 execution.",
            "Probe is not yet connected to producer imports/collation in same child.",
            "Bubblewrap installation/version/hash and user namespaces unverified.",
            "Host root remains readable; not a confidentiality sandbox.",
            "Trusted producer boundary; no protection against hostile host races.",
            "Fresh private output avoids preexisting hardlinks, but native path "
            "and dependency behavior still require verified host tests.",
            "Upstream main sources checked for API only, not deployed binary evidence.",
            "No native backward/resource/efficacy/novelty gate passed.",
            "Shared diagnostic implementation does not advance M197 recovery."])
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
        candidate.update(
            retry_after=RETRY, blocker=BLOCKER,
            unblock_condition="Verified server-4 runtime/data/GPU and pinned bwrap; "
                "real scratch probe and same-child native integration pass. M197 "
                "separately requires checkpoint compatibility and safe admission.")
        candidate["scratch_boundary_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"],
            tests_skipped=len(result.skipped), physical_bindings_verified=9,
            model_geometry_captures=0, native_execution_completed=False,
            scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; static/mocked sandbox launcher "
                "implementation, failure tests and upstream mount-layout review.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/"
                "GPU0/1 before read-only M197 last.pth retrieval; validate optimizer/"
                "epoch/path compatibility before safe resume admission. Preserve "
                "stopped_unknown; no server-6 restart. Shared sandbox tests are "
                "not checkpoint recovery or efficacy evidence.")
            candidate["latest_progress"] = now + ": SSH refused; no checkpoint recovery."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = (
                now + ": Scratch probe launcher statically/mocked tested; "
                "Linux enforcement unverified, physical9/model0 unchanged.")
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Missing due record")
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(found), evidence=[entry],
        next_action=NEXT, result="Scratch launcher implemented/tested; native blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temporary = "pipeline/research_work.scratch_boundary_1715.tmp"
    write_new(temporary, work)
    os.replace(ROOT / temporary, ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=REPORT, tests=result.testsRun,
                         passed=report["validation"]["tests_passed"],
                         skipped=len(result.skipped))))


if __name__ == "__main__":
    main()
