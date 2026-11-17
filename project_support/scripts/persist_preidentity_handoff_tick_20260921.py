"""Persist the synthetic pre-identity handoff tick without promoting native gates."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


REPORT = "pipeline/reports/preidentity_handoff_progress_20260921-1215.json"
PRIOR = "pipeline/reports/preidentity_loader_progress_20260921-1115.json"
RETRY = "2026-09-21T13:07:00+08:00"
BLOCKER = (
    "One scheduled server-4 SSH attempt refused port22. No remote command ran; "
    "runtime, GPU occupancy, installed dependency bytes/ABI, assets and Linux "
    "isolation remain unverified. Synthetic handoff tests are not native validation.")
NEXT = (
    "Continue the existing diagnostic, no new review or variant. Build and test "
    "the independently pinned bootstrap/launcher manifest producer that consumes "
    "PreIdentityHandoff, including whole-child timeout/output bounds and immutable "
    "artifact handoff, using synthetic children only. On the authorized host, "
    "inventory installed dependency/bootstrap roots and extension shared-library "
    "provenance without asserting ABI from hashes. Retry server-4 once at/after "
    + RETRY + ". With verified host, held GPU0/1 slot, dependency/assets/isolation "
    "and3 artifacts/6 data hashes, collate saved3040/3893 and exact replay, then "
    "export3921/4278 retaining31. Never regenerate recovered groups or run legacy "
    "server-6/GPU7 CLI.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-21T04:07:06.694210+00:00"):
        raise ValueError("Wrong event snapshot")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Missing decision")
    if ROOT / REPORT in [ROOT / p for p in []]:
        raise ValueError("Unreachable")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    prior = read(PRIOR)
    modules = ["test_preidentity_handoff_20260921"] + prior["validation"]["modules"]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Regression failed")
    paths = [
        PRIOR, args.decision, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/pinned_diagnostic_imports_20260920.py",
        "scripts/saved_physical_location_20260920.py",
        "scripts/preidentity_handoff_20260921.py",
        "scripts/test_preidentity_handoff_20260921.py",
        "scripts/persist_preidentity_handoff_tick_20260921.py",
    ]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now,
        snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=1,
            command=("ssh -o BatchMode=yes -o ConnectTimeout=8 "
                     "-o ConnectionAttempts=1 songcl@192.168.1.137 hostname"),
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            evidence_basis="Observed exec_command this tick; no scripted retry",
            runtime_verified=False, gpu_occupancy_verified=False),
        completed_work=[
            "Added a single-use PreIdentityHandoff around the existing pinned Torch loader.",
            "The handoff file and all dependency/bootstrap rows require independent SHA256 values.",
            "Every pre-existing non-stdlib bootstrap module must have an exact name/path/hash row.",
            "The boundary remains active through logical GPU identity collection.",
            "Held-slot and execution checks bracket import, CUDA identity and successful return.",
            "Failures poison/discard the child; imported native modules are never rolled back.",
            "Sixteen focused handoff tests and the bounded regression passed synthetically.",
            "No queue/checkpoint/data/model mutation and no native execution."],
        validation=dict(
            tests_run=result.testsRun,
            tests_passed=result.testsRun - len(result.skipped),
            new_tests=16, modules=modules,
            skipped=[dict(test=str(t), reason=r) for t, r in result.skipped],
            output=stream.getvalue(), native_data_loaded=False),
        physical_bindings_verified=9, physical_bindings_missing=22,
        registry_denominator=31, model_geometry_captures=0,
        native_execution_completed=False, scientific_validation_complete=False,
        native_backward_verified=False, resources_verified=False,
        admission=False, training_launch=False, checkpoint_transfer=False,
        queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Bootstrap file hashes do not attest the bytes already executed by the parent interpreter.",
            "An independently pinned launcher/bootstrap must generate and enforce the handoff.",
            "Extension shared-library dependencies and native ABI remain unverified.",
            "The loader is a trusted-code boundary, not a sandbox or zero-CUDA-side-effect proof.",
            "Whole-child CPU, wall-time and output limits are caller-owned and not yet integrated.",
            "No actual GPU identity, native forward/backward/resources/efficacy or admission evidence.",
            "Shared M95 implementation does not recover M197."])
    work = read("pipeline/research_work.json")
    due = set(context["research_work"]["due_ids"])
    if due != {c["id"] for c in work["candidates"] if c["id"] in due}:
        raise ValueError("Missing due candidates")
    write_new(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    for candidate in work["candidates"]:
        if candidate["id"] not in due:
            continue
        merged = {e["path"]: e for e in candidate["evidence"]}
        merged.update({e["path"]: e for e in evidence + [entry]})
        candidate.update(
            evidence=list(merged.values()), blocker=BLOCKER, retry_after=RETRY,
            next_action=NEXT,
            unblock_condition=(
                "Verified authorized server-4 runtime, held GPU0/1 slot, independently "
                "pinned bootstrap/launcher and installed dependency/shared-library "
                "provenance, assets and Linux isolation. M197 separately requires "
                "checkpoint/optimizer/epoch/path and resume admission."),
            latest_progress=now + ":hash-pinned fresh-child handoff implemented/tested synthetically.")
        candidate["preidentity_handoff_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"],
            tests_skipped=len(result.skipped), native_execution_completed=False,
            scientific_validation_complete=False,
            alternatives_attempted=(
                "One SSH refusal;16 new synthetic handoff/coordinator tests plus "
                "bounded regression. No native packages/data or unauthorized hosts."))
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/GPU0/1 "
                "before read-only M197 checkpoint recovery; validate optimizer/epoch/paths "
                "and safe resume admission. Preserve stopped_unknown; no server-6 restart. "
                "Shared M95 loader does not recover M197.")
            candidate["latest_progress"] = now + ":SSH refused; M197 recovery blocked."
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(due), evidence=[entry],
        next_action=NEXT,
        result="Pre-identity handoff implemented/tested synthetically; native work blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.preidentity_handoff_1215.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
