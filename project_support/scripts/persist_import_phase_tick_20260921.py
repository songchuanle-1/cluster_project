"""Persist bounded import-phase evidence; no execution or admission promotion."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from model_execution_inventory_20260921 import import_execution_audit
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


REPORT = "pipeline/reports/import_phase_progress_20260921-1012.json"
PRIOR = "pipeline/reports/logical_identity_progress_20260921-0912.json"
RETRY = "2026-09-21T11:07:00+08:00"
BLOCKER = (
    "One scheduled server-4 SSH attempt refused port22; no remote command ran. "
    "Installed dependency paths/bytes/ABI, GPU occupancy, destination assets and "
    "Linux isolation remain unverified. Static import audit is not runtime proof.")
NEXT = (
    "Continue the existing diagnostic, not another review or variant. Implement "
    "the pre-identity Torch-only loader in the existing pinned-import boundary "
    "with explicit independently supplied dependency paths/hashes, fresh-child "
    "preimport rejection and postimport origin/source checks; test using synthetic "
    "packages only locally. Do not call this native ABI verification. Keep model/"
    "extension imports after physical/logical identity agreement; resolve the "
    "observed sample_model sys.path mutation with exact origin checks, not a "
    "baseline source rewrite. Retry server-4 once at/after " + RETRY + ". On a "
    "verified host and held GPU0/1 slot, verify actual dependencies/ABI/assets/"
    "isolation and3 artifacts/6 data hashes; collate saved3040/3893, exact replay, "
    "then export3921/4278 retaining31. Never regenerate recovered groups or "
    "execute legacy server-6/GPU7 CLI.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-21T02:07:10.333362+00:00"):
        raise ValueError("Wrong event snapshot")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Missing decision")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_import_phase_audit_20260921"] + read(PRIOR)["validation"]["modules"]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Regression failed")
    audit = import_execution_audit(ROOT / "Cluster")
    migration = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for row in read(migration)["evidence"]:
        if file_sha256(ROOT / row["path"]) != row["sha256"]:
            raise ValueError("Migration evidence drift")
    paths = [PRIOR, migration, args.decision, "pipeline/goal.json", "SERVERS.yaml",
             "scripts/model_execution_inventory_20260921.py",
             "scripts/test_import_phase_audit_20260921.py",
             "scripts/persist_import_phase_tick_20260921.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now,
        snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=1,
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            evidence_basis="Observed exec_command this tick; no scripted retry",
            runtime_verified=False, gpu_occupancy_verified=False),
        import_audit=audit,
        validation=dict(
            tests_run=result.testsRun, tests_passed=result.testsRun-len(result.skipped),
            new_tests=13, modules=modules,
            skipped=[dict(test=str(t), reason=r) for t, r in result.skipped],
            output=stream.getvalue(), native_data_loaded=False),
        physical_bindings_verified=9, physical_bindings_missing=22,
        registry_denominator=31, model_geometry_captures=0,
        native_execution_completed=False, scientific_validation_complete=False,
        admission=False, training_launch=False, checkpoint_transfer=False,
        queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=audit["limitations"] + [
            "Shared M95 static audit does not recover M197.",
            "No native forward/backward, resource, efficacy or admission evidence."])
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
            unblock_condition="Authorized server-4 runtime and held GPU0/1 slot, "
                "physical/logical UUID agreement, verified dependency paths/bytes/"
                "native ABI and offline assets/destination bytes/Linux isolation. "
                "M197 additionally needs optimizer/epoch/path and safe resume checks.",
            latest_progress=now + ":31-source import-phase audit; physical9/model0 unchanged.")
        candidate["import_phase_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"],
            tests_skipped=len(result.skipped), native_execution_completed=False,
            scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal;31-source static import-phase "
                "audit,13 local source-fixture tests and bounded regression.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/"
                "GPU0/1 before read-only M197 checkpoint recovery; validate optimizer/"
                "epoch/paths and safe resume admission. Preserve stopped_unknown; "
                "no server-6 restart. Shared M95 audit does not recover M197.")
            candidate["latest_progress"] = now + ":SSH refused; M197 recovery blocked."
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(due), evidence=[entry],
        next_action=NEXT, result="Import-phase audit completed; native work blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.import_phase_1012.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
