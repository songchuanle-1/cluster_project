from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "pipeline/reports/due_capture_readiness_20260919-1409.json"
WORK_PATH = ROOT / "pipeline/research_work.json"
PERMUTATION_REPORT = (
    ROOT / "pipeline/reports/referent_permutation_calibration_20260919-1409.json"
)
CALIBRATION_SOURCE = ROOT / "scripts/referent_permutation_calibration_20260919.py"
CALIBRATION_TEST = ROOT / "scripts/test_referent_permutation_calibration_20260919.py"
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
    timestamp = "2026-09-19T14:09:00+08:00"
    observed_at = "2026-09-19T14:08:00+08:00"
    retry_after = "2026-09-19T15:07:00+08:00"
    unblock_condition = (
        "M197-PIRS reaches terminal state or GPU7 has fewer than two processes "
        "with sufficient measured free memory."
    )
    blocker = (
        "At 2026-09-19T14:08:00+08:00, GPU7 remained at the two-process cap "
        "with M197-PIRS pid1134192 (19956 MiB) plus foreign pid3827570 "
        "(42488 MiB), with 18597 MiB free. Native candidate scoring remains "
        "unavailable."
    )

    calibration = json.loads(PERMUTATION_REPORT.read_text(encoding="utf-8"))
    null_familywise = calibration["null"]["summary"]["holm_familywise_any"]
    signal_familywise = calibration["planted_signal"]["summary"][
        "holm_familywise_any"
    ]
    if calibration["decision"]["status"] != "passed":
        raise SystemExit("corrected permutation calibration did not pass")

    report = {
        "schema_version": 1,
        "scope": (
            "Capacity-only retry plus a CPU-side correction to the permutation "
            "family-wise endpoint; no model forward, native capture, training, "
            "queue mutation, or efficacy claim"
        ),
        "generated_at": timestamp,
        "remote_observation": {
            "timestamp": observed_at,
            "server": "server-6",
            "gpu": 7,
            "memory_total_mib": 81559,
            "memory_used_mib": 62483,
            "memory_free_mib": 18597,
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
            "observed_at": "2026-09-19T14:07:10+08:00",
            "source": ".tick_context preflight",
            "epoch": 22,
            "total_epochs": 50,
            "best_miou": 0.4910,
            "no_improve": 1,
            "no_improve_limit": 10,
            "process_alive": True,
        },
        "blocker": {
            "blocker": blocker,
            "retry_after": retry_after,
            "unblock_condition": unblock_condition,
        },
        "attempted_alternatives": [
            "Queried the live GPU7 process table and memory without touching "
            "any process.",
            "Audited the existing permutation-calibration family-wise summary "
            "instead of repeating an earlier capacity-only check.",
            "Corrected the Holm family-wise endpoint from all endpoints "
            "rejecting (max) to any endpoint rejecting (min).",
            "Added a regression test and reran the 300-simulation by 999-draw "
            "calibration.",
            "Kept native capture unlaunched because the frozen producer gate "
            "still requires an open GPU slot.",
        ],
        "native_capture_launched": False,
        "static_research_progress": {
            "status": "corrected_and_retested_this_tick",
            "finding": (
                "The previous family-wise endpoint required all six adjusted "
                "p-values to reject, which measured joint rejection rather "
                "than family-wise any rejection. The corrected min rule gives "
                "an honest null estimate of 10/300 and unchanged planted "
                "signal detection of 300/300."
            ),
            "permutation_calibration": {
                "report": PERMUTATION_REPORT.relative_to(ROOT).as_posix(),
                "report_sha256": sha256(PERMUTATION_REPORT),
                "source": {
                    "path": CALIBRATION_SOURCE.relative_to(ROOT).as_posix(),
                    "sha256": sha256(CALIBRATION_SOURCE),
                },
                "test": {
                    "path": CALIBRATION_TEST.relative_to(ROOT).as_posix(),
                    "sha256": sha256(CALIBRATION_TEST),
                    "tests_passed": 4,
                    "tests_failed": 0,
                },
                "null_familywise_any": null_familywise,
                "planted_signal_familywise_any": signal_familywise,
                "decision": calibration["decision"],
            },
        },
    }

    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report_hash = sha256(REPORT_PATH)
    permutation_report_hash = sha256(PERMUTATION_REPORT)
    source_hash = sha256(CALIBRATION_SOURCE)
    test_hash = sha256(CALIBRATION_TEST)

    with WORK_PATH.open("r", encoding="utf-8") as handle:
        work = json.load(handle)

    by_id = {candidate["id"]: candidate for candidate in work["candidates"]}
    missing = [
        candidate_id
        for candidate_id in CANDIDATE_IDS
        if candidate_id not in by_id
    ]
    if missing:
        raise SystemExit(f"missing candidates: {missing}")

    latest = (
        f"{timestamp}: the due retry found M197-PIRS pid1134192 (19956 MiB) "
        "plus foreign pid3827570 (42488 MiB) on server-6 GPU7, so the "
        "two-process cap remains closed. CPU work corrected the permutation "
        "family-wise endpoint from max to min, added a regression test, and "
        "reran the full calibration: null family-wise 10/300 with 95% upper "
        "bound 0.06026; planted-signal family-wise 300/300. Fresh evidence: "
        f"pipeline/reports/{REPORT_PATH.name} sha256={report_hash}."
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
        "report": f"pipeline/reports/{REPORT_PATH.name}",
        "report_sha256": report_hash,
        "gpu_process_count": 2,
        "gpu_free_mib": 18597,
        "m197_epoch": 22,
        "m197_best_miou": 0.4910,
        "native_execution_completed": False,
        "cpu_validation_tests_passed": 4,
        "finding": (
            "Due retry remained gated by M197-PIRS and foreign pid3827570; "
            "the permutation family-wise summary was corrected and retested."
        ),
        "retry_after": retry_after,
    }
    permutation_progress = {
        "timestamp": timestamp,
        "report": PERMUTATION_REPORT.relative_to(ROOT).as_posix(),
        "report_sha256": permutation_report_hash,
        "simulations": calibration["settings"]["simulations"],
        "permutation_draws": calibration["settings"]["permutation_draws"],
        "familywise_null_rejection_rate": null_familywise["rejection_rate"],
        "familywise_null_upper_ci95": null_familywise[
            "rejection_rate_ci95"
        ]["high"],
        "referent_top1_power": calibration["planted_signal"]["summary"][
            "referent_top1"
        ]["rejection_rate"],
        "referent_normalized_excess_power": calibration["planted_signal"][
            "summary"
        ]["referent_normalized_excess"]["rejection_rate"],
        "familywise_planted_signal_power": signal_familywise[
            "rejection_rate"
        ],
        "objectness_top1_false_positive_rate": calibration[
            "planted_signal"
        ]["summary"]["objectness_top1"]["rejection_rate"],
        "native_execution_completed": False,
        "status": "passed_cpu_calibration_after_familywise_fix",
        "correction": (
            "Family-wise any rejection now uses min(adjusted p-values) <= "
            "alpha, not max(adjusted p-values) <= alpha."
        ),
        "source_sha256": source_hash,
        "test_sha256": test_hash,
    }
    evidence_entries = [
        {
            "path": f"pipeline/reports/{REPORT_PATH.name}",
            "sha256": report_hash,
        },
        {
            "path": PERMUTATION_REPORT.relative_to(ROOT).as_posix(),
            "sha256": permutation_report_hash,
        },
    ]
    reconciled_hashes = {
        CALIBRATION_SOURCE.relative_to(ROOT).as_posix(): source_hash,
        CALIBRATION_TEST.relative_to(ROOT).as_posix(): test_hash,
    }
    for candidate in work["candidates"]:
        for entry in candidate.get("evidence", []):
            if entry.get("path") in reconciled_hashes:
                entry["sha256"] = reconciled_hashes[entry["path"]]

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
        candidate["permutation_calibration_progress"] = permutation_progress
        evidence = candidate.setdefault("evidence", [])
        for entry in evidence_entries:
            if entry not in evidence:
                evidence.append(entry)

    work["last_event_tick"] = {
        "timestamp": timestamp,
        "mode": "event",
        "due_ids": CANDIDATE_IDS,
        "result": (
            "The 14:07 GPU7 retry still found M197-PIRS plus foreign "
            "pid3827570 at the two-process cap with 18597 MiB free. No native "
            "capture was launched. CPU work corrected the permutation "
            "family-wise rejection rule and regenerated the full calibration."
        ),
        "next_action": next_action,
        "evidence": evidence_entries,
    }

    temp_path = WORK_PATH.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(work, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temp_path, WORK_PATH)

    with WORK_PATH.open("r", encoding="utf-8") as handle:
        verified = json.load(handle)
    verified_by_id = {
        candidate["id"]: candidate
        for candidate in verified["candidates"]
    }
    for candidate_id in CANDIDATE_IDS:
        candidate = verified_by_id[candidate_id]
        if candidate.get("retry_after") != retry_after:
            raise SystemExit(f"{candidate_id}: retry time was not persisted")
        if candidate.get("permutation_calibration_progress") != permutation_progress:
            raise SystemExit(
                f"{candidate_id}: corrected calibration was not persisted"
            )
        for entry in evidence_entries:
            if entry not in candidate.get("evidence", []):
                raise SystemExit(f"{candidate_id}: evidence was not persisted")

    print(
        json.dumps(
            {
                "report": {
                    "path": f"pipeline/reports/{REPORT_PATH.name}",
                    "sha256": report_hash,
                },
                "updated_candidates": CANDIDATE_IDS,
                "m197": report["m197_snapshot_progress"],
                "permutation_calibration": permutation_progress,
                "post_write_validation": "ok",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
