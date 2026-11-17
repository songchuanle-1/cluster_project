from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "pipeline/reports/native_chain_recovery_20260919-1612.json"
SELFTEST_PATH = (
    ROOT / "pipeline/reports/referent_native_chain_selftest_20260919-1507.json"
)
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    timestamp = "2026-09-19T16:12:15+08:00"
    observed_at = "2026-09-19T16:11:28+08:00"
    retry_after = "2026-09-19T17:07:00+08:00"
    unblock_condition = (
        "M197-PIRS reaches terminal state or GPU7 has fewer than two processes "
        "with sufficient measured free memory."
    )
    blocker = (
        "At 2026-09-19T16:11:28+08:00, GPU7 remained at the two-process cap "
        "with M197-PIRS pid1134192 (19956 MiB) plus foreign pid3827570 "
        "(42488 MiB), with 18597 MiB free. Native candidate scoring remains "
        "unavailable."
    )

    selftest = json.loads(SELFTEST_PATH.read_text(encoding="utf-8"))
    mismatches = []
    for entry in selftest["source_hashes"]:
        if sha256(ROOT / entry["path"]) != entry["sha256"]:
            mismatches.append(entry["path"])
    if mismatches:
        raise SystemExit(f"self-test source hash mismatch: {mismatches}")
    if not all(check.get("passed") is True for check in selftest["checks"]):
        raise SystemExit("self-test contains a failed check")

    report = {
        "schema_version": 1,
        "scope": (
            "Event recovery of the interrupted 15:07 native-chain validation; "
            "no model forward, native score, queue mutation, training launch, "
            "admission, or efficacy claim"
        ),
        "generated_at": timestamp,
        "remote_observation": {
            "timestamp": observed_at,
            "server": "server-6",
            "gpu": 7,
            "memory_total_mib": 81559,
            "memory_used_mib": 62483,
            "memory_free_mib": 18597,
            "utilization_percent": 93,
            "process_count_on_gpu": 2,
            "processes": [
                {
                    "pid": 1134192,
                    "process_name": "python",
                    "used_memory_mib": 19956,
                    "role": "M197-PIRS",
                },
                {
                    "pid": 3827570,
                    "process_name": "/home/jiaoh/conda_envs/das_env/bin/python",
                    "used_memory_mib": 42488,
                    "role": "foreign",
                },
            ],
        },
        "m197_snapshot_progress": {
            "observed_at": "2026-09-19T16:07:10+08:00",
            "source": ".tick_context preflight",
            "epoch": 23,
            "total_epochs": 50,
            "best_miou": 0.4918,
            "no_improve": 0,
            "no_improve_limit": 10,
            "process_alive": True,
        },
        "blocker": {
            "blocker": blocker,
            "retry_after": retry_after,
            "unblock_condition": unblock_condition,
        },
        "recovered_artifact": {
            "path": SELFTEST_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256(SELFTEST_PATH),
            "checks_passed": len(selftest["checks"]),
            "source_entries": len(selftest["source_hashes"]),
            "source_hash_mismatches": 0,
            "recovery_finding": (
                "The interrupted 15:07 tick left a complete synthetic "
                "native-chain self-test with matching producer, projection, "
                "evaluator, coverage, and permutation-control hashes; the "
                "current 59-test contract suite passes."
            ),
        },
        "cpu_validation": {
            "command": (
                "python -m unittest "
                "test_referent_native_expression_producer_20260919 "
                "test_referent_object_rank_capture_20260919 "
                "test_referent_target_rank_evaluator_20260919 "
                "test_referent_query_coverage_control_20260919 "
                "test_referent_within_scene_permutation_20260919 "
                "test_referent_permutation_calibration_20260919"
            ),
            "tests_passed": 59,
            "tests_failed": 0,
        },
        "native_capture_launched": False,
        "recovery_status": "persisted",
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report_hash = sha256(REPORT_PATH)
    selftest_hash = sha256(SELFTEST_PATH)

    with WORK_PATH.open("r", encoding="utf-8") as handle:
        work = json.load(handle)
    by_id = {candidate["id"]: candidate for candidate in work["candidates"]}
    missing = [candidate_id for candidate_id in CANDIDATE_IDS if candidate_id not in by_id]
    if missing:
        raise SystemExit(f"missing candidates: {missing}")

    latest = (
        f"{timestamp}: event recovery verified the interrupted 15:07 synthetic "
        "native-chain self-test against the current 12 source hashes and reran "
        "59 focused contract tests successfully. The live GPU7 retry still "
        "found M197-PIRS pid1134192 plus foreign pid3827570 at the two-process "
        "cap, so native capture remains blocked. Recovered evidence: "
        f"{SELFTEST_PATH.relative_to(ROOT).as_posix()} sha256={selftest_hash}; "
        f"recovery report: {REPORT_PATH.relative_to(ROOT).as_posix()} "
        f"sha256={report_hash}."
    )
    next_action = (
        f"Retry after {retry_after}. When GPU7 has capacity, run the frozen M95 "
        "native capture, require the frozen producer and capture-derived "
        "binding, project rows, build the object-rank capture, and evaluate "
        "rank/coverage plus the corrected calibrated permutation control. "
        "Reject any expression with missing candidate, query, support-size, "
        "cost, mask, or seed coverage without imputation. If the exact-"
        "coverage gate is not met, do not promote the all-candidate rank "
        "contrast; retain exact-coverage and calibrated permutation results "
        "only as diagnostics."
    )
    capacity_progress = {
        "timestamp": timestamp,
        "report": REPORT_PATH.relative_to(ROOT).as_posix(),
        "report_sha256": report_hash,
        "gpu_process_count": 2,
        "gpu_free_mib": 18597,
        "m197_epoch": 23,
        "m197_best_miou": 0.4918,
        "native_execution_completed": False,
        "cpu_validation_tests_passed": 59,
        "finding": (
            "Event recovery preserved the interrupted native-chain self-test "
            "and confirmed its source hashes; GPU7 remains capped."
        ),
        "retry_after": retry_after,
    }
    recovery_progress = {
        "timestamp": timestamp,
        "report": REPORT_PATH.relative_to(ROOT).as_posix(),
        "report_sha256": report_hash,
        "self_test_report": SELFTEST_PATH.relative_to(ROOT).as_posix(),
        "self_test_sha256": selftest_hash,
        "self_test_checks_passed": len(selftest["checks"]),
        "source_hash_mismatches": 0,
        "cpu_validation_tests_passed": 59,
        "native_execution_completed": False,
        "status": "interrupted_artifact_recovered_and_verified",
    }
    evidence_entries = [
        {
            "path": REPORT_PATH.relative_to(ROOT).as_posix(),
            "sha256": report_hash,
        },
        {
            "path": SELFTEST_PATH.relative_to(ROOT).as_posix(),
            "sha256": selftest_hash,
        },
    ]

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
        candidate["native_chain_recovery_progress"] = recovery_progress
        evidence = candidate.setdefault("evidence", [])
        for entry in evidence_entries:
            if entry not in evidence:
                evidence.append(entry)

    work["last_event_tick"] = {
        "timestamp": timestamp,
        "mode": "event",
        "due_ids": CANDIDATE_IDS,
        "result": (
            "Recovered the interrupted 15:07 synthetic native-chain self-test, "
            "verified all 12 source hashes, reran 59 contract tests, and found "
            "GPU7 still at the two-process cap. No native capture was launched."
        ),
        "next_action": next_action,
        "evidence": evidence_entries,
    }

    temp_path = WORK_PATH.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(work, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temp_path, WORK_PATH)

    verified = json.loads(WORK_PATH.read_text(encoding="utf-8"))
    verified_by_id = {
        candidate["id"]: candidate for candidate in verified["candidates"]
    }
    for candidate_id in CANDIDATE_IDS:
        candidate = verified_by_id[candidate_id]
        if candidate.get("retry_after") != retry_after:
            raise SystemExit(f"{candidate_id}: retry time was not persisted")
        if candidate.get("native_chain_recovery_progress") != recovery_progress:
            raise SystemExit(f"{candidate_id}: recovery progress was not persisted")
        if evidence_entries[0] not in candidate.get("evidence", []):
            raise SystemExit(f"{candidate_id}: recovery evidence was not persisted")

    print(
        json.dumps(
            {
                "report": {
                    "path": REPORT_PATH.relative_to(ROOT).as_posix(),
                    "sha256": report_hash,
                },
                "recovered_selftest": {
                    "path": SELFTEST_PATH.relative_to(ROOT).as_posix(),
                    "sha256": selftest_hash,
                },
                "updated_candidates": CANDIDATE_IDS,
                "tests_passed": 59,
                "post_write_validation": "ok",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
