"""Persist actual static audit and regression evidence for the 06:07 event."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from model_execution_inventory_20260921 import inventory
from persist_import_boundary_tick_20260920 import read, write_new
from saved_dependency_inventory_20260921 import inventory as cpu_inventory
from saved_replay_migration_20260920 import ROOT


REPORT = "pipeline/reports/model_inventory_progress_20260921-0615.json"
PRIOR = "pipeline/reports/relocated_driver_progress_20260921-0515.json"
RETRY = "2026-09-21T07:07:00+08:00"
NEXT = (
    "Continue the same saved diagnostic, not a new variant/review. Model-side audit "
    "now records constructor weights, checkpoint load contract, default CUDA device "
    "and external framework/native dependencies. Next resolve the explicit "
    "framework.utils/torch and pointnet2 import boundaries listed in the audit, "
    "and implement/test GPU runtime observation validation without weakening the "
    "existing CPU CUDA-hidden validator. Reuse existing runtime/capacity checks; "
    "do not add another orchestration wrapper or substitute model constructors. "
    "Retry server-4 once at/after " + RETRY + ". If reachable verify interpreter/"
    "code/data/work paths, physical GPU0/1 UUID/occupancy and held slot, actual "
    "model weights/checkpoint/native ABI and Linux enforcement before loading. "
    "Verify3 relocated artifacts/6 data hashes; collate3040/3893 and exact saved "
    "replay, then export3921/4278 retaining31. Never regenerate recovered groups "
    "or execute legacy server-6/GPU7 CLI.")
BLOCKER = (
    "One scheduled server-4 SSH attempt refused port22. Native runtime/GPU/"
    "destination bytes/weights/checkpoint/extensions/isolation remain unverified. "
    "Static model audit and synthetic tests are not native execution or admission; "
    "production GPU execution validator and model callback still pending.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T22:07:07.659725+00:00"):
        raise ValueError("Wrong tick")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Decision missing")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_model_execution_inventory_20260921"] + read(PRIOR)["validation"]["modules"]
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not tests.wasSuccessful():
        raise ValueError("Regression failed")
    model = inventory(ROOT / "Cluster")
    cpu = cpu_inventory(ROOT / "Cluster")
    migration = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for row in read(migration)["evidence"]:
        if file_sha256(ROOT / row["path"]) != row["sha256"]:
            raise ValueError("Original migration evidence drift")
    paths = [
        PRIOR, migration, args.decision, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/model_execution_inventory_20260921.py",
        "scripts/test_model_execution_inventory_20260921.py",
        "scripts/persist_model_inventory_tick_20260921.py",
        "scripts/saved_dependency_inventory_20260921.py",
        "scripts/cpu_diagnostic_bootstrap_20260920.py",
        "scripts/native_saved_geometry_driver_20260920.py",
        "scripts/relocated_geometry_driver_20260921.py",
        "scripts/saved_physical_location_20260920.py"]
    paths += ["Cluster/" + row["path"] for row in model["sources"] + [model["config"]]]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(server="server-4", attempts=1, returncode=1,
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            evidence_basis="Observed exec_command this tick; no scripted retry",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(tests_run=tests.testsRun,
            tests_passed=tests.testsRun-len(tests.skipped), modules=modules, new_tests=8,
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            output=stream.getvalue(), native_data_loaded=False),
        model_inventory=model, cpu_inventory=cpu,
        completed_work=[
            "Audited nine actual model/framework sources and one original config.",
            "Reused CPU AST parser and re-evaluated existing five-source CPU inventory.",
            "Identified pretrained model weights needed before full checkpoint load.",
            "Recorded spconv/pointnet2/external framework and default-device requirements.",
            "Specified before-load, before-allocation and after-capture checks.",
            "Eight new synthetic tests and bounded existing regression completed."],
        physical_bindings_verified=9, physical_bindings_missing=22,
        registry_denominator=31, model_geometry_captures=0,
        native_execution_completed=False, scientific_validation_complete=False,
        admission=False, training_launch=False, checkpoint_transfer=False,
        production_execution_validator_implemented=False, queue_changed=False,
        queue_sha256=queue_hash, blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"])
    work = read("pipeline/research_work.json")
    due = set(context["research_work"]["due_ids"])
    if due != {c["id"] for c in work["candidates"] if c["id"] in due}:
        raise ValueError("Missing candidate")
    write_new(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    for candidate in work["candidates"]:
        if candidate["id"] not in due:
            continue
        merged = {e["path"]: e for e in candidate["evidence"]}
        merged.update({e["path"]: e for e in evidence + [entry]})
        candidate.update(evidence=list(merged.values()), blocker=BLOCKER,
            retry_after=RETRY,
            unblock_condition="Verified server-4 runtime/allocation/slot, destination "
                "and model weights/checkpoint/native dependencies/Linux enforcement. "
                "M197 independently needs compatible checkpoint and safe resume admission.")
        candidate["model_inventory_progress"] = dict(timestamp=now, report=REPORT,
            report_sha256=entry["sha256"], tests_passed=report["validation"]["tests_passed"],
            tests_skipped=len(tests.skipped), native_execution_completed=False,
            scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; actual bounded source audit and "
                "eight synthetic tests plus existing regression; no native work.")
        candidate["next_action"] = NEXT
        candidate["latest_progress"] = now + ": Model dependency audit done; physical9/model0 unchanged."
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/GPU0/1 "
                "before read-only M197 checkpoint recovery; validate optimizer/epoch/"
                "paths and safe resume admission. Preserve stopped_unknown; no "
                "server-6 restart. M95 model audit does not recover M197.")
            candidate["latest_progress"] = now + ": SSH refused; checkpoint recovery blocked."
    work["last_event_tick"] = dict(timestamp=now, mode="event",
        due_ids=sorted(due), evidence=[entry], next_action=NEXT,
        result="Model dependency audit/test completed; native access blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.model_inventory_0615.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
