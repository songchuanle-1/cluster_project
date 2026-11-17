from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "pipeline/reports/due_capture_readiness_20260919-0442.json"
WORK_PATH = ROOT / "pipeline/research_work.json"
CANDIDATE_IDS = [
    "referent-causality-audit",
    "modality-identity-preservation",
    "referent-discrimination",
    "instance-identity-representation",
    "referent-query-selection",
    "input-modality-distinguishability",
    "same-target-description-grounding",
]
TEST_PATHS = [
    ROOT / "scripts/test_referent_native_expression_producer_20260919.py",
    ROOT / "scripts/test_referent_object_rank_capture_20260919.py",
    ROOT / "scripts/test_referent_target_rank_evaluator_20260919.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    timestamp = "2026-09-19T04:42:00+08:00"
    observed_at = "2026-09-19T04:42:46+08:00"
    retry_after = "2026-09-19T05:25:00+08:00"
    blocker = (
        "At 2026-09-19T04:42:46+08:00, GPU7 remained at the two-process cap "
        "with M197-PIRS pid1134192 (19956 MiB) plus foreign pid3827570 "
        "(42488 MiB), with 18597 MiB free. The frozen registry, object-capture "
        "adapter, and native-expression producer are implemented, but native "
        "candidate scoring remains unavailable."
    )
    unblock_condition = (
        "M197-PIRS reaches terminal state or GPU7 has fewer than two processes "
        "with sufficient measured free memory."
    )
    report = {
        "schema_version": 1,
        "scope": (
            "Capacity-only retry plus CPU-side frozen pipeline validation; no "
            "model forward, capture, training, queue mutation, or efficacy claim"
        ),
        "timestamp": timestamp,
        "remote_observation": {
            "timestamp": observed_at,
            "server": "server-6",
            "gpu": 7,
            "utilization_percent": 100,
            "used_mib": 62483,
            "total_mib": 81559,
            "free_mib": 18597,
            "processes": [
                {
                    "pid": 1134192,
                    "process_name": "python",
                    "used_mib": 19956,
                    "role": "M197-PIRS",
                },
                {
                    "pid": 3827570,
                    "process_name": "/home/jiaoh/conda_envs/das_env/bin/python",
                    "used_mib": 42488,
                    "role": "foreign",
                },
            ],
        },
        "m197_live_progress": {
            "observed_at": observed_at,
            "source": "unique M197 log tail with carriage returns normalized",
            "epoch": 20,
            "total_epochs": 50,
            "step": 2799,
            "total_steps": 4686,
            "best_miou": 0.486,
            "best_validation_epoch": 19,
            "no_improve": 0,
            "no_improve_limit": 10,
            "process_alive": True,
        },
        "blocker": {
            "blocker": blocker,
            "retry_after": retry_after,
            "unblock_condition": unblock_condition,
        },
        "attempted_alternatives": [
            "Waited until the recorded retry time before rechecking capacity.",
            "Queried the live GPU7 process table and memory without touching any process.",
            "Normalized and inspected the unique M197 log tail to verify native step progress.",
            "Ran all 30 frozen producer, object-rank capture, and evaluator tests this tick.",
            "Kept native capture unlaunched because the two-process cap remained closed.",
        ],
        "native_capture_launched": False,
        "cpu_validation": {
            "status": "passed_this_tick",
            "command": (
                "python -m unittest "
                "test_referent_native_expression_producer_20260919 "
                "test_referent_object_rank_capture_20260919 "
                "test_referent_target_rank_evaluator_20260919"
            ),
            "tests_passed": 30,
            "tests_failed": 0,
            "suites": [
                {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)}
                for path in TEST_PATHS
            ],
        },
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report_hash = sha256(REPORT_PATH)

    with WORK_PATH.open("r", encoding="utf-8") as handle:
        work = json.load(handle)

    by_id = {candidate["id"]: candidate for candidate in work["candidates"]}
    missing = [candidate_id for candidate_id in CANDIDATE_IDS if candidate_id not in by_id]
    if missing:
        raise SystemExit(f"missing candidates: {missing}")

    latest = (
        f"{timestamp}: the due retry found M197-PIRS pid1134192 (19956 MiB) "
        "plus foreign pid3827570 (42488 MiB) on server-6 GPU7, so the "
        "two-process cap remained closed. M197 advanced to epoch 20 and native "
        "step 2799/4686; epoch 19 validation reported mIoU 0.486 and best.pth "
        "was saved. All 30 frozen producer, object-rank capture, and evaluator "
        "tests passed this tick. Fresh evidence: "
        f"pipeline/reports/{REPORT_PATH.name} sha256={report_hash}."
    )
    evidence_entry = {
        "path": f"pipeline/reports/{REPORT_PATH.name}",
        "sha256": report_hash,
    }
    capacity_progress = {
        "timestamp": timestamp,
        "report": evidence_entry["path"],
        "report_sha256": report_hash,
        "gpu_process_count": 2,
        "gpu_free_mib": 18597,
        "m197_epoch": 20,
        "native_step": 2799,
        "native_total_steps": 4686,
        "native_execution_completed": False,
        "cpu_validation_tests_passed": 30,
        "finding": (
            "Due retry remained gated by M197-PIRS and foreign pid3827570; "
            "M197 advanced to epoch 20, step 2799/4686."
        ),
        "retry_after": retry_after,
    }
    next_action = (
        f"Retry after {retry_after}. When GPU7 has capacity, run the frozen M95 "
        "native capture, project its rows with "
        "scripts/referent_native_expression_producer_20260919.py, pass the projection "
        "through scripts/referent_object_rank_capture_20260919.py and "
        "scripts/referent_target_rank_evaluator_20260919.py, and reject any "
        "expression with missing candidate or seed coverage without imputation. "
        "Keep the 31 observed-failure pairs separate as failure-local diagnostics."
    )

    for candidate_id in CANDIDATE_IDS:
        candidate = by_id[candidate_id]
        if candidate.get("stage") != "blocked":
            raise SystemExit(
                f"{candidate_id}: expected blocked, found {candidate.get('stage')!r}"
            )
        candidate["blocker"] = blocker
        candidate["retry_after"] = retry_after
        candidate["unblock_condition"] = unblock_condition
        candidate["latest_progress"] = latest
        candidate["next_action"] = next_action
        candidate["capacity_retry_progress"] = capacity_progress
        evidence = candidate.setdefault("evidence", [])
        if evidence_entry not in evidence:
            evidence.append(evidence_entry)

    temp_path = WORK_PATH.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(work, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temp_path, WORK_PATH)

    with WORK_PATH.open("r", encoding="utf-8") as handle:
        verified = json.load(handle)
    verified_by_id = {candidate["id"]: candidate for candidate in verified["candidates"]}
    for candidate_id in CANDIDATE_IDS:
        candidate = verified_by_id[candidate_id]
        if candidate.get("retry_after") != retry_after:
            raise SystemExit(f"{candidate_id}: retry time was not persisted")
        if evidence_entry not in candidate.get("evidence", []):
            raise SystemExit(f"{candidate_id}: evidence was not persisted")

    print(
        json.dumps(
            {
                "report": evidence_entry,
                "updated_candidates": CANDIDATE_IDS,
                "m197": report["m197_live_progress"],
                "cpu_validation": report["cpu_validation"],
                "post_write_validation": "ok",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
