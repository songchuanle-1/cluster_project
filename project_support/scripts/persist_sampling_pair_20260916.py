"""Persist executed sampling checks and bounded archived-support audit."""
import hashlib
import json
from pathlib import Path
import unittest
from sampling_pair_contract_20260916 import sampling_paired_summary

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def evidence(path):
    return dict(path=path, sha256=hashlib.sha256((ROOT / path).read_bytes()).hexdigest())


if __name__ == "__main__":
    modules = ["test_sampling_pair_contract_20260916", "test_frozen_capture_contract_20260916",
               "test_paired_capture_evaluation_20260916", "test_native_endpoint_capture_20260916",
               "test_native_support_capture_20260916", "test_capture_support_20260916",
               "test_physical_mask_endpoints_20260916"]
    result = unittest.TextTestRunner().run(unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromName(name) for name in modules))
    if not result.wasSuccessful():
        raise SystemExit(1)
    source = "pipeline/reports/native_support_capture_20260916-1517.json"
    rows = read(source)["rows"]
    try:
        sampling_paired_summary(rows, rows, baseline_checkpoint="a" * 64,
                                candidate_checkpoint="a" * 64)
    except ValueError as exc:
        rejection = str(exc)
    else:
        raise AssertionError("Old archive must fail exact-input gate")
    for row in rows:
        fps, indices = row["fps_superpoints"], row["sampled_seed_indices"]
        assert len(indices) == len(row["scores"])
        assert all(type(x) is int and 0 <= x < len(row["original_superpoint_ids"]) for x in fps)
        assert all(type(x) is int and 0 <= x < len(fps) for x in indices)
    paths = ["scripts/sampling_pair_contract_20260916.py",
             "scripts/test_sampling_pair_contract_20260916.py",
             "scripts/persist_sampling_pair_20260916.py",
             "pipeline/decisions/20260916-211108_other.md", source]
    blocker = dict(
        blocker="GPU7 has PIRS PID1134192 and foreign PID3827570; two-process limit reached.",
        retry_after="2026-09-16T22:07:00+08:00",
        unblock_condition="Fewer than two GPU7 processes and sufficient measured free memory.",
        alternatives_attempted="Implemented sampling pairing checks, ran56tests, audited archived FPS binding.")
    report_path = "pipeline/reports/sampling_pair_20260916-2112.json"
    report = dict(
        scope="Static pairing implementation and archived support audit only",
        tests_passed=result.testsRun, new_tests_passed=6,
        archive_rows_valid_sampling=len(rows), archive_strict_rejection=rejection,
        native_execution_completed=False, scientific_validation_complete=False,
        remote_observation=dict(gpu=7, used_mib=62473, free_mib=18607,
                                utilization_percent=100, pids=[1134192, 3827570],
                                epoch=9, native_train_steps=[857, 858], capture_launched=False),
        blocker=blocker, evidence=[evidence(path) for path in paths],
        limitations=["Recorded FPS equality is necessary, not proof of all RNG equality.",
                     "Learned query selection is not conditioned on; model source audit remains due.",
                     "No native semantic/control capture, terminal PIRS comparison or efficacy result."])
    (ROOT / report_path).write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    context = read("pipeline/headless/.tick_context.json")
    work = read("pipeline/research_work.json")
    for candidate in work["candidates"]:
        if candidate["id"] not in context["research_work"]["due_ids"]:
            continue
        candidate["evidence"].extend(evidence(path) for path in paths[:4] + [report_path])
        candidate["sampling_pair_progress"] = dict(report=report_path, tests_passed=result.testsRun,
            native_execution_completed=False, scientific_validation_complete=False)
        candidate["native_capture_blocker"] = blocker
        if candidate["id"] in ("modality-identity-preservation",
                               "instance-identity-representation", "input-modality-distinguishability"):
            candidate["next_action"] = (
                "Retry GPU7 at2026-09-16T22:07:00+08:00; require fewer than two processes "
                "and sufficient free memory. Execute frozen TRAIN semantic sample, then "
                "recoverable same-class feature contrasts. Validate FPS support with "
                "sampling_pair_contract_20260916; do not condition on learned selections.")
    (ROOT / "pipeline/research_work.json").write_text(
        json.dumps(work, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps(dict(report=report_path, archive_rows=len(rows), tests=result.testsRun)))
