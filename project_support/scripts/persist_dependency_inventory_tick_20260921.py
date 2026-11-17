"""Persist the bounded saved-collation dependency audit and regression evidence."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_dependency_inventory_20260921 import inventory
from saved_replay_migration_20260920 import ROOT


PRIOR = "pipeline/reports/host_preparation_progress_20260921-0115.json"
REPORT = "pipeline/reports/dependency_inventory_progress_20260921-0215.json"
RETRY = "2026-09-21T03:07:00+08:00"
NEXT = (
    "Continue the existing saved-only diagnostic, not a new mechanism. Static direct "
    "dependency/constructor requirements are now enumerated, not runtime-attested. "
    "Next implement and test a single host handoff adapter connecting prepare_handoff "
    "to complete_handoff with independent original binding/full31 digest/saved indices, "
    "without exposing native CLI or bypassing deployment checks. Retry server-4 once "
    "at/after " + RETRY + "; verify runtime/code/data/work paths and GPU0/1 occupancy. "
    "On verified access, measure direct/transitive package and shared-library identity, "
    "actual pointgroup_ops extension ABI/hash, all tokenizer assets and nonempty TRAIN "
    "*_refer.pth listing; verify3 artifacts/6 data hashes. Validate Linux process-group "
    "cleanup/bwrap enforcement before saved3040/3893 collation; separate location-aware "
    "prepare_replay remains next. Then export3921/4278 retaining full31; never regenerate "
    "saved groups. Local remains static/synthetic only.")
BLOCKER = (
    "Scheduled server-4 SSH attempt refused port22. Destination runtime/GPU/data/"
    "extension ABI and bwrap/kernel remain unverified. Direct dependency checklist "
    "is finite but not complete transitive closure or checkpoint recovery.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T18:07:07.582253+00:00"):
        raise ValueError("Wrong tick")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Current decision required")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    audit = inventory(ROOT / "Cluster")
    modules = ["test_saved_dependency_inventory_20260921"] + read(PRIOR)["validation"]["modules"]
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
    if inventory(ROOT / "Cluster") != audit:
        raise ValueError("Audit changed during regression")
    paths = [
        PRIOR, migration, args.decision, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/saved_dependency_inventory_20260921.py",
        "scripts/test_saved_dependency_inventory_20260921.py",
        "scripts/persist_dependency_inventory_tick_20260921.py",
        "scripts/relocated_native_factory_20260920.py",
        "scripts/prepare_collation_handoff_20260921.py",
        "scripts/bounded_collation_process_20260921.py",
    ] + ["Cluster/" + row["path"] for row in audit["sources"]]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=1,
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            command="ssh -o BatchMode=yes -o ConnectTimeout=10 -o ConnectionAttempts=1 songcl@192.168.1.137 hostname",
            evidence_basis="Observed exec_command this tick; no scripted retry",
            runtime_verified=False, gpu_occupancy_verified=False),
        dependency_audit=audit,
        validation=dict(
            tests_run=tests.testsRun, tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            modules=modules, new_tests=10, output=stream.getvalue(),
            initial_failure="Windows newline mismatch in missing-import fixture; corrected to text replacement.",
            native_data_loaded=False, bubblewrap_execution=False,
            linux_process_group_test_executed=False),
        completed_work=[
            "Five exact dataset/local-extension sources statically parsed and rehashed.",
            "Nine direct external package roots enumerated with source/line evidence.",
            "Relative pointgroup_ops extension and unresolved framework dynamic imports exposed.",
            "Nonempty TRAIN *_refer.pth directory listing identified as constructor precondition.",
            "Existing graph cache, all tokenizer files, label map and TRAIN annotations retained.",
            "Ten new static/synthetic tests plus full bounded regression.",
            "Original migration evidence rehashed; no original producer mutation."],
        registry_denominator=31, physical_bindings_verified=9, physical_bindings_missing=22,
        model_geometry_captures=0, external_dependency_attestation=False,
        destination_bytes_verified=False, native_cli_completed=False,
        native_cpu_execution=False, native_gpu_execution=False, checkpoint_transfer=False,
        training_tree_sync=False, training_launch=False, admission=False,
        scientific_validation_complete=False, queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=audit["limitations"] + [
            "No local native execution, packages imported or datasets inspected.",
            "Source checklist is not measured scientific diagnosis or dependency attestation.",
            "M197 checkpoint recovery remains separate and blocked."])
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
            unblock_condition="Verified authorized server-4 runtime/GPU/bwrap/kernel, "
                "destination bytes, actual extension ABI and native dependencies before "
                "saved collation. M197 separately needs compatible checkpoint/safe admission.")
        candidate["dependency_inventory_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(tests.skipped),
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; five-source static dependency/"
                "constructor audit and ten synthetic tests; no unauthorized native work.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/GPU0/1 "
                "before read-only M197 last.pth retrieval; validate optimizer/epoch/path "
                "compatibility before safe resume admission. Preserve stopped_unknown; "
                "no server-6 restart. Dependency checklist is not checkpoint recovery.")
            candidate["latest_progress"] = now + ": SSH refused; checkpoint recovery blocked."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = now + ": Direct dependencies audited; physical9/model0 unchanged."
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Missing due record")
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(found), evidence=[entry],
        next_action=NEXT, result="Bounded source dependency audit completed; native access blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.dependency_inventory_0215.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
