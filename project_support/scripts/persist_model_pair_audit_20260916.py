"""Persist bounded static audit; no queue or training changes."""
import hashlib
import json
from pathlib import Path
import unittest
from model_pair_audit_20260916 import audit

ROOT = Path(__file__).resolve().parents[1]


def evidence(path):
    return dict(path=path, sha256=hashlib.sha256((ROOT / path).read_bytes()).hexdigest())


if __name__ == "__main__":
    modules = ["test_model_pair_audit_20260916", "test_sampling_pair_contract_20260916",
               "test_frozen_capture_contract_20260916", "test_paired_capture_evaluation_20260916",
               "test_native_endpoint_capture_20260916", "test_native_support_capture_20260916",
               "test_capture_support_20260916", "test_physical_mask_endpoints_20260916"]
    result = unittest.TextTestRunner().run(unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromName(name) for name in modules))
    if not result.wasSuccessful():
        raise SystemExit(1)
    report = audit(ROOT)
    report["tests_passed"] = result.testsRun
    report["remote_observation"] = dict(
        gpu=7, used_mib=62473, free_mib=18607, utilization_percent=100,
        pids=[1134192, 3827570], epoch=9, native_steps=[1854, 1860],
        capture_launched=False)
    blocker = dict(
        blocker="GPU7 has two processes, PIRS1134192 and foreign3827570.",
        retry_after="2026-09-16T23:07:00+08:00",
        unblock_condition="Fewer than two GPU7 processes and sufficient measured free memory.",
        alternatives_attempted="Executed source AST audit and60static tests; "
                               "identified uncaptured hierarchical sampling.")
    report["blocker"] = blocker
    paths = ["scripts/model_pair_audit_20260916.py",
             "scripts/test_model_pair_audit_20260916.py",
             "scripts/persist_model_pair_audit_20260916.py",
             "pipeline/decisions/20260916-221056_other.md"]
    report["evidence"].extend(evidence(path) for path in paths)
    report_path = "pipeline/reports/model_pair_audit_20260916-2211.json"
    (ROOT / report_path).write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    context = json.loads((ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8"))
    path = ROOT / "pipeline/research_work.json"
    work = json.loads(path.read_text(encoding="utf-8"))
    for candidate in work["candidates"]:
        if candidate["id"] not in context["research_work"]["due_ids"]:
            continue
        candidate["evidence"].extend(evidence(p) for p in paths + [report_path])
        candidate["model_pair_audit_progress"] = dict(
            report=report_path, tests_passed=result.testsRun,
            native_execution_completed=False, scientific_validation_complete=False)
        candidate["native_capture_blocker"] = blocker
        candidate["next_action"] = candidate["next_action"].replace(
            "2026-09-16T22:07:00+08:00", "2026-09-16T23:07:00+08:00")
        candidate["next_action"] += (
            " Before native pairing, instrument hierarchical partition outputs "
            "alongside entry FPS and bind PIRS model class; compare frozen geometry "
            "without conditioning on learned selections.")
    path.write_text(json.dumps(work, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps(dict(report=report_path, tests=result.testsRun,
                          changed_loss_methods=report["changed_loss_methods"])))
