"""Record tested event continuation; no native execution, queue or host mutation."""
import argparse
from datetime import datetime
import io
import json
import os
import unittest

from frozen_capture_contract_20260916 import file_sha256
from saved_replay_migration_20260920 import ROOT

REPORT = "pipeline/reports/location_progress_20260920-1215.json"
PRIOR = "pipeline/reports/migration_progress_20260920-1015.json"
NEXT = (
    "At/after 2026-09-20T13:07:00+08:00 retry server-4 SSH once. Before any transfer "
    "or native execution verify GPU0/1 occupancy/memory, native code root, "
    "project_cluster environment and data paths. Retrieve saved3040/3893 bytes "
    "read-only from server-6; do not run source-host diagnostics. Verify all3 "
    "destination artifacts,6 data hashes and immutable producer/model/checkpoint/"
    "dataset binding. Integrate SavedPhysicalLocation into a separate server-4 "
    "native CPU collation entrypoint, preserve original provenance and full31 rows, "
    "then prepare exact replay and export3921/4278. Legacy driver hardcodes GPU7 "
    "and must not run unchanged. Local next executable work if SSH remains blocked: "
    "synthetic integration of relocated items through existing native-collation "
    "callback contract, with byte-bound output and failure cleanup tests; do not "
    "duplicate location validators or regenerate saved groups. Connect capacity "
    "observation validator to fresh server-4 measurements plus actual coordination "
    "before GPU allocation; boolean callback checks alone are not a reservation. "
    "Physical9/31 and model0/31 unchanged; no admission.")
BLOCKER = (
    "One server-4 SSH attempt in this event was refused on port22. Authorized "
    "runtime/data, GPU occupancy, destination artifact bytes and checkpoints "
    "remain unverified. Constraint17 forbids new native work on server-6 and "
    "local is static/orchestration only. Relocated loader and capacity predicate "
    "passed synthetic tests but native collation CLI and real capacity coordination "
    "are not yet integrated; no destination execution was performed.")


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_new(path, value):
    with (ROOT / path).open("x", encoding="ascii") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    context = read("pipeline/headless/.tick_context.json")
    if (context["generated_at"] != "2026-09-20T04:07:08.192151+00:00"
            or context["mode"] != "event"):
        raise ValueError("Wrong event snapshot")
    decision = (ROOT / args.decision).resolve()
    if not decision.is_relative_to(ROOT / "pipeline/decisions"):
        raise ValueError("Project decision required")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    work_hash = file_sha256(ROOT / "pipeline/research_work.json")
    modules = ["test_saved_physical_location_20260920"] + read(PRIOR)["validation"]["modules"]
    if len(modules) != len(set(modules)):
        raise ValueError("Duplicate regression modules")
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not tests.wasSuccessful():
        raise ValueError("Regression failed")
    contract = "pipeline/reports/saved_replay_migration_20260920-1015.json"
    for item in read(contract)["evidence"]:
        if file_sha256(ROOT / item["path"]) != item["sha256"]:
            raise ValueError("Original migration evidence changed: " + item["path"])
    paths = [
        contract, PRIOR, args.decision, "scripts/saved_physical_location_20260920.py",
        "scripts/test_saved_physical_location_20260920.py",
        "scripts/persist_location_tick_20260920.py", "pipeline/goal.json", "SERVERS.yaml",
    ]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    now = datetime.now().astimezone().isoformat()
    report = dict(
        schema_version=1, generated_at=now, snapshot_generated_at=context["generated_at"],
        mode="event", resumed_due_ids=context["research_work"]["due_ids"], evidence=evidence,
        connectivity=dict(server="server-4", host="192.168.1.137", port=22, attempts=1,
            command="ssh -o BatchMode=yes -o ConnectTimeout=8 -o ConnectionAttempts=1 songcl@192.168.1.137 hostname",
            returncode=1, stderr="ssh: connect to host 192.168.1.137 port 22: Connection refused",
            gpu_occupancy_verified=False, runtime_verified=False),
        validation=dict(
            tests_run=tests.testsRun, tests_passed=tests.testsRun-len(tests.skipped),
            skipped=[dict(test=str(t), reason=r) for t, r in tests.skipped],
            modules=modules, output=stream.getvalue(), focused_tests_passed=28,
            new_tests=18, local_native_data_loaded=False),
        completed_work=[
            "Implemented separate relocated saved-item loader for exact3040/3893.",
            "Validated original contract against source physical metadata without changing provenance.",
            "Verified synthetic3 artifact/6 data byte observations before load and again after load.",
            "Preserved exact31 registry identities,4 bound/27 missing and original source binding.",
            "Checked loaded original indices,input fingerprints,axes count and reconstructed full bindings.",
            "Implemented synthetic server-4 GPU0/1 freshness,idleness,memory and coordination predicate.",
            "Rehashed original migration evidence; retained existing M197 interruption analysis."],
        registry_denominator=31, physical_bindings_verified=9, physical_bindings_missing=22,
        model_geometry_captures=0, destination_bytes_verified=False,
        native_cpu_execution=False, native_gpu_execution=False, native_collation_completed=False,
        checkpoint_transfer=False, training_tree_sync=False, training_launch=False,
        admission=False, scientific_validation_complete=False,
        queue_changed=False, queue_sha256=queue_hash,
        pending_questions_24h=context["manifests"]["pending_questions_24h"],
        open_questions=[
            "When will server-4 SSH and native runtime be restored?",
            "Will relocated data/checkpoints and native source hashes match the frozen source?",
            "M197 resume requires checkpoint optimizer/epoch and path compatibility verification."],
        blocker=BLOCKER, next_action=NEXT, retry_after="2026-09-20T13:07:00+08:00",
        limitations=[
            "Callbacks were mocked; no real destination bytes were read or transferred.",
            "Synthetic payloads and exporter do not prove native tensor or full binding reconstruction.",
            "Native CPU collation/prepare_replay CLI integration remains executable follow-up.",
            "Capacity predicate is not an OS lock,reservation,live GPU observation or dispatch receipt.",
            "No model forward/backward,efficiency,causal effect or novel mechanism validated.",
            "M197 is blocked on separate checkpoint/runtime recovery,not advanced by loader tests."])
    write_new(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    work = read("pipeline/research_work.json")
    found = set()
    for candidate in work["candidates"]:
        if candidate["id"] not in context["research_work"]["due_ids"]:
            continue
        found.add(candidate["id"])
        merged = {row["path"]: row for row in candidate["evidence"]}
        merged.update({row["path"]: row for row in evidence + [entry]})
        candidate["evidence"] = list(merged.values())
        candidate["blocker"] = BLOCKER
        candidate["retry_after"] = report["retry_after"]
        candidate["unblock_condition"] = (
            "server-4 SSH/runtime/GPU0/1/data verified; destination saved bytes and immutable "
            "sources match, native collation entrypoint integrated and tested. M197 separately "
            "requires validated checkpoint plus safe resume admission/dispatch.")
        candidate["location_adapter_progress"] = dict(
            timestamp=now, report=REPORT, report_sha256=entry["sha256"],
            tests_passed=report["validation"]["tests_passed"], tests_skipped=len(tests.skipped),
            physical_bindings_verified=9, model_geometry_captures=0,
            native_execution_completed=False, scientific_validation_complete=False,
            alternatives_attempted="One SSH refusal; completed local synthetic location loader "
                "and capacity predicate tests without using unauthorized hosts.")
        if candidate["id"] == "referent-supervision-axis":
            candidate["next_action"] = (
                "No restart on server-6. At/after2026-09-20T13:07:00+08:00 verify server-4 "
                "SSH/GPU0/1/runtime/data. Then retrieve and validate M197 last.pth read-only "
                "with optimizer/epoch/path compatibility before any server-4 resume through "
                "the safe gated dispatch path. Preserve stopped_unknown; interruption is not "
                "efficacy or novelty. Location adapter tests do not validate M197 recovery.")
            candidate["latest_progress"] = now + ": SSH refused; no checkpoint transfer/resume; existing interruption retained."
        else:
            candidate["next_action"] = NEXT
            candidate["latest_progress"] = now + ": Synthetic relocated loader/capacity checks passed; physical9/31 and model0/31 unchanged."
    if found != set(context["research_work"]["due_ids"]):
        raise ValueError("Due candidate missing")
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=context["research_work"]["due_ids"],
        evidence=[entry], next_action=NEXT,
        result="Synthetic location adapter completed; native collation and host access remain incomplete")
    if (file_sha256(ROOT / "pipeline/research_work.json") != work_hash
            or file_sha256(ROOT / "pipeline/queue.json") != queue_hash):
        raise ValueError("Concurrent state mutation")
    temporary = "pipeline/research_work.location_1215.tmp"
    write_new(temporary, work)
    os.replace(ROOT / temporary, ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=REPORT, tests=tests.testsRun, skipped=len(tests.skipped))))


if __name__ == "__main__":
    main()
