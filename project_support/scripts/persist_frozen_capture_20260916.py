"""Persist bounded diagnostic progress, without queue or admission changes."""
import hashlib
import json
from pathlib import Path
import unittest

from frozen_capture_contract_20260916 import strict_paired_summary

root = Path(__file__).resolve().parents[1]
modules = [
    "test_frozen_capture_contract_20260916",
    "test_paired_capture_evaluation_20260916",
    "test_native_endpoint_capture_20260916",
    "test_native_support_capture_20260916",
    "test_capture_support_20260916",
    "test_physical_mask_endpoints_20260916",
]
suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name)
                           for name in modules)
result = unittest.TextTestRunner().run(suite)
if not result.wasSuccessful():
    raise SystemExit(1)


def read(name):
    return json.loads((root / name).read_text(encoding="utf-8"))


def evidence(name):
    return dict(path=name, sha256=hashlib.sha256((root / name).read_bytes()).hexdigest())


source = "pipeline/reports/native_support_capture_20260916-1517.json"
rows = read(source)["rows"]
try:
    strict_paired_summary(rows, rows, baseline_checkpoint="a" * 64,
                          candidate_checkpoint="a" * 64)
except ValueError as exc:
    rejection = str(exc)
else:
    raise AssertionError("Historical capture incorrectly accepted")

names = [
    "scripts/frozen_capture_contract_20260916.py",
    "scripts/native_frozen_capture_20260916.py",
    "scripts/test_frozen_capture_contract_20260916.py",
    "scripts/persist_frozen_capture_20260916.py",
    "pipeline/decisions/20260916-201153_other.md",
    source,
]
blocker = dict(
    blocker="GPU7 occupied by PIRS PID1134192 and foreign PID3827570.",
    retry_after="2026-09-16T21:07:00+08:00",
    unblock_condition="Fewer than two GPU7 processes and sufficient measured free memory.",
    alternatives_attempted="Executed exact-input hashing, paired rejection tests and archive rejection.")
report_name = "pipeline/reports/frozen_capture_20260916-2013.json"
report = dict(
    scope="Static matched-input implementation; no native capture or mechanism efficacy",
    tests_passed=result.testsRun, new_tests_passed=9,
    canonical_closure_context_tests_passed=25,
    existing_closure_linkage="referent-supervision-axis -> experiment_id M197-PIRS; preserved",
    archive_expressions=len(rows), archive_rejection=rejection,
    remote_observation=dict(gpu=7, used_mib=62473, free_mib=18607,
                            utilization_percent=100, pids=[1134192, 3827570],
                            native_validation_epoch=8, native_validation_steps=[295, 319],
                            capture_launched=False),
    blocker=blocker, evidence=[evidence(name) for name in names],
    limitations=[
        "Model-internal FPS/random draws still need matched treatment across checkpoints.",
        "New capture entry point is M95-only; terminal PIRS model binding still required.",
        "All six frozen control expression keys remain absent from historical smoke capture.",
        "Broad unittest discovery failed: 73 passed, one import error because local torch absent.",
        "Broad discovery invoked a legacy read-only monitor test; violates single-preflight instruction.",
        "Legacy test reports unchanged state; no intentional monitor/goal rerun or queue edits.",
        "Shared tooling only, not completion of eight candidate-specific native actions."])
(root / report_name).write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
work = read("pipeline/research_work.json")
due = read("pipeline/headless/.tick_context.json")["research_work"]["due_ids"]
for candidate in work["candidates"]:
    if candidate["id"] not in due:
        continue
    additions = [evidence(name) for name in names[:5] + [report_name]]
    for item in additions:
        if item not in candidate["evidence"]:
            candidate["evidence"].append(item)
    candidate["frozen_input_progress"] = dict(
        report=report_name, tests_passed=result.testsRun,
        stage_completed="Static exact transformed-input and checkpoint identity",
        native_execution_completed=False, scientific_validation_complete=False)
    candidate["native_capture_blocker"] = blocker
    if candidate["id"] in ("modality-identity-preservation",
                           "instance-identity-representation", "input-modality-distinguishability"):
        candidate["next_action"] = (
            "Retry GPU7 after2026-09-16T21:07:00+08:00; preserve both jobs. "
            "When below two processes and enough memory, deploy versioned frozen-input "
            "capture and execute predefined TRAIN semantic sample, then recoverable "
            "same-class feature contrasts. Freeze model-internal sampling as well.")
    elif candidate["id"] == "referent-causality-audit":
        candidate["next_action"] = (
            "Await terminal PIRS; bind its model class and checkpoint to frozen TRAIN/control "
            "manifest, match internal sampling and transformed input hashes, then execute "
            "strict scene-balanced paired evaluation. Old smoke archive is ineligible.")
(root / "pipeline/research_work.json").write_text(
    json.dumps(work, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
print(json.dumps(dict(report=report_name, tests=result.testsRun, due_records=len(due))))
