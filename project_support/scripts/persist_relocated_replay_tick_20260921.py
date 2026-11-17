"""Record tested saved-replay implementation without advancing native gates."""
import argparse
from datetime import datetime
import io
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from persist_import_boundary_tick_20260920 import read, write_new
from saved_replay_migration_20260920 import ROOT


PRIOR = "pipeline/reports/prepared_execution_progress_20260921-0315.json"
REPORT = "pipeline/reports/relocated_replay_progress_20260921-0415.json"
RETRY = "2026-09-21T05:07:00+08:00"
NEXT = (
    "Continue the existing saved diagnostic, not a new mechanism. Location-aware "
    "prepare_relocated_replay is synthetically tested but not wired to native execution. "
    "Next statically integrate it with a separate server-4 saved geometry driver using "
    "existing replay_forward and native capacity/source checks; test exact saved indices, "
    "original producer binding, full31 joins, failure publication and no resampling. "
    "Do not execute the legacy server-6/GPU7 CLI. Retry server-4 once at/after " + RETRY +
    ". On verified access check runtime/code/data/work paths and GPU0/1 occupancy; "
    "verify actual dependencies/extension ABI/assets,3 saved artifacts/6 data hashes "
    "and Linux group cleanup/bwrap enforcement. Supply a real execution validator "
    "before native adapter launch. Then collate3040/3893 and prepare saved replay; "
    "export3921/4278 retaining31. Never regenerate recovered groups.")
BLOCKER = (
    "One scheduled server-4 SSH attempt refused port22. Runtime/GPU/data/checkpoints/"
    "dependencies/Linux enforcement remain unverified. Relocated replay tests are "
    "synthetic only, not native capture, admission or checkpoint recovery.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["mode"] != "event"
            or context["generated_at"] != "2026-09-20T20:07:07.506700+00:00"):
        raise ValueError("Wrong tick")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions") or not decision.is_file():
        raise ValueError("Current decision required")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_relocated_saved_replay_20260921"] + read(PRIOR)["validation"]["modules"]
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
        PRIOR, migration, args.decision, "pipeline/goal.json", "SERVERS.yaml",
        "scripts/relocated_saved_replay_20260921.py",
        "scripts/test_relocated_saved_replay_20260921.py",
        "scripts/persist_relocated_replay_tick_20260921.py",
        "scripts/saved_geometry_replay_20260920.py",
        "scripts/saved_physical_location_20260920.py",
        "scripts/scratch_collation_launch_20260920.py"]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(
            server="server-4", attempts=1, returncode=1,
            stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            command='ssh -o BatchMode=yes -o ConnectTimeout=8 -o ConnectionAttempts=1 '
                    'songcl@192.168.1.137 "hostname"',
            evidence_basis="Observed exec_command this tick; no scripted retry",
            runtime_verified=False, gpu_occupancy_verified=False),
        validation=dict(
            tests_run=tests.testsRun, tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            modules=modules, new_tests=16, output=stream.getvalue(),
            native_data_loaded=False, bubblewrap_execution=False),
        completed_work=[
            "Location-aware saved-replay adapter consumes published collation receipts and batches.",
            "Independent original binding/full31 digest/indices checked before saved-item loading.",
            "Reuses original location loader and replay payload/axis verification; no resampling.",
            "Requires exact migration locations and counts; retains original producer/source binding.",
            "Rechecks all receipt bytes, inputs, prepared objects and source after loading.",
            "Sixteen synthetic tests cover real collation output to prepared replay plus failure cases."],
        registry_denominator=31, physical_bindings_verified=9, physical_bindings_missing=22,
        model_geometry_captures=0, relocated_replay_adapter_implemented=True,
        native_driver_integration=False, production_execution_validator_implemented=False,
        destination_bytes_verified=False, native_cpu_execution=False,
        native_gpu_execution=False, checkpoint_transfer=False, training_tree_sync=False,
        training_launch=False, admission=False, scientific_validation_complete=False,
        queue_changed=False, queue_sha256=queue_hash,
        blocker=BLOCKER, next_action=NEXT, retry_after=RETRY,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        limitations=[
            "Location source inspections/exporter are mocked; synthetic pickle payloads only.",
            "Callbacks are trusted, not a sandbox or authorization boundary.",
            "No protection against actively hostile host filesystem races.",
            "No native forward/backward, GPU measurements or scientific efficacy evidence.",
            "M197 checkpoint recovery remains independently blocked."])
    work = read("pipeline/research_work.json")
    found = {c["id"] for c in work["candidates"]
             if c["id"] in context["research_work"]["due_ids"]}
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Missing due record")
    write_new(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    for candidate in work["candidates"]:
        if candidate["id"] not in found:
            continue
        merged = {e["path"]: e for e in candidate["evidence"]}
        merged.update({e["path"]: e for e in evidence + [entry]})
        candidate.update(
            evidence=list(merged.values()), retry_after=RETRY, blocker=BLOCKER,
            unblock_condition="Verified authorized server-4 runtime/GPU, bwrap/kernel, "
                "destination bytes and actual dependencies; real execution validator "
                "required before native launch. M197 needs compatible checkpoint/safe admission.")
        candidate["relocated_replay_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(tests.skipped),
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; implemented/tested location-aware saved "
                "replay with16 new synthetic tests and bounded regression; no native work.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "Retry server-4 once at/after " + RETRY + ". Verify runtime/data/GPU0/1 "
                "before read-only M197 last.pth retrieval; validate optimizer/epoch/path "
                "compatibility before safe resume admission. Preserve stopped_unknown; "
                "no server-6 restart. Shared replay adapter is not checkpoint recovery.")
            candidate["latest_progress"] = now + ": SSH refused; checkpoint recovery blocked."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = now + ": Saved replay tested; physical9/model0 unchanged."
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=sorted(found), evidence=[entry],
        next_action=NEXT, result="Relocated replay implemented/tested; native access blocked.")
    if (file_sha256(ROOT / "pipeline/queue.json") != queue_hash
            or file_sha256(ROOT / "pipeline/research_work.json") != work_hash):
        raise ValueError("Concurrent state mutation")
    temp = "pipeline/research_work.relocated_replay_0415.tmp"
    write_new(temp, work)
    os.replace(ROOT / temp, ROOT / "pipeline/research_work.json")
    print(REPORT)


if __name__ == "__main__":
    main()
