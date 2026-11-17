from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "pipeline/reports/due_capture_readiness_20260919-0711.json"
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
    ROOT / "scripts/test_referent_query_coverage_control_20260919.py",
]
STATIC_PATHS = [
    ROOT / "scripts/referent_object_rank_capture_20260919.py",
    ROOT / "scripts/referent_query_coverage_control_20260919.py",
    ROOT / "scripts/test_referent_object_rank_capture_20260919.py",
    ROOT / "scripts/test_referent_query_coverage_control_20260919.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    timestamp = "2026-09-19T07:12:00+08:00"
    observed_at = "2026-09-19T07:10:43+08:00"
    retry_after = "2026-09-19T08:07:00+08:00"
    blocker = (
        "At 2026-09-19T07:10:43+08:00, GPU7 remained at the two-process cap "
        "with M197-PIRS pid1134192 (19956 MiB) plus foreign pid3827570 "
        "(42488 MiB), with 18597 MiB free. The frozen registry, object-capture "
        "adapter, native-expression producer, query-coverage control, and "
        "dual-balance contract are implemented, but native candidate scoring "
        "remains unavailable."
    )
    unblock_condition = (
        "M197-PIRS reaches terminal state or GPU7 has fewer than two processes "
        "with sufficient measured free memory."
    )
    report = {
        "schema_version": 1,
        "scope": (
            "Capacity-only retry plus CPU-side dual-balance matched-control "
            "derivation; no model forward, native capture, training, queue "
            "mutation, or efficacy claim"
        ),
        "timestamp": timestamp,
        "remote_observation": {
            "timestamp": observed_at,
            "server": "server-6",
            "gpu": 7,
            "utilization_percent": 100,
            "used_mib": 62483,
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
        "m197_snapshot_progress": {
            "observed_at": "2026-09-19T07:07:11+08:00",
            "source": ".tick_context preflight",
            "epoch": 21,
            "total_epochs": 50,
            "best_miou": 0.4910,
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
            "Queried the live GPU7 process table and memory without touching "
            "any process.",
            "Identified object extent as a second plausible best-of-k "
            "confounder not controlled by query-count matching alone.",
            "Persisted each object's native support size in the frozen object-"
            "rank capture contract.",
            "Predeclared a descriptive dual-balanced subset requiring exact "
            "query-count and object-support-size matches.",
            "Ran all 40 producer, object-rank, evaluator, coverage, and "
            "dual-balance tests; kept native capture unlaunched.",
        ],
        "native_capture_launched": False,
        "static_research_progress": {
            "status": "implemented_and_tested_this_tick",
            "finding": (
                "Exact query-count matching controls the number of scores "
                "available to each object, but it does not control object "
                "extent. The frozen capture now records support size, and the "
                "audit predeclares a stricter dual-balanced subset before "
                "native scores exist."
            ),
            "coverage_gate": {
                "min_exact_match_rate": 0.75,
                "max_mean_abs_coverage_delta": 1.0,
                "min_matched_scenes": 2,
                "consequence_if_not_met": (
                    "Do not promote the all-candidate rank contrast; retain the "
                    "exact-coverage matched contrast as diagnostic evidence."
                ),
            },
            "support_balance_control": {
                "status": "secondary_sensitivity_control_not_admission_gate",
                "match_fields": [
                    "native_query_count",
                    "object_support_size",
                ],
                "consequence": (
                    "Report the dual-balanced subset and paired contrast; never "
                    "replace or promote it over the primary exact-coverage "
                    "result."
                ),
            },
            "source_hashes": [
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": sha256(path),
                }
                for path in STATIC_PATHS
            ],
        },
        "cpu_validation": {
            "status": "passed_this_tick",
            "command": (
                "python -m unittest "
                "test_referent_native_expression_producer_20260919 "
                "test_referent_object_rank_capture_20260919 "
                "test_referent_target_rank_evaluator_20260919 "
                "test_referent_query_coverage_control_20260919"
            ),
            "tests_passed": 40,
            "tests_failed": 0,
            "suites": [
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": sha256(path),
                }
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
        "two-process cap remains closed. Static work added native object "
        "support-size recording and a predeclared dual-balanced sensitivity "
        "subset for exact query count plus object extent. All 40 producer, "
        "object-rank, evaluator, coverage, and dual-balance tests passed this "
        f"tick. Fresh evidence: pipeline/reports/{REPORT_PATH.name} "
        f"sha256={report_hash}."
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
        "m197_epoch": 21,
        "m197_best_miou": 0.4910,
        "native_execution_completed": False,
        "cpu_validation_tests_passed": 40,
        "dual_balance_tests_passed": 3,
        "finding": (
            "Due retry remained gated by M197-PIRS and foreign pid3827570; "
            "object support size is now captured for a stricter sensitivity "
            "control."
        ),
        "retry_after": retry_after,
    }
    dual_balance_progress = {
        "timestamp": timestamp,
        "report": evidence_entry["path"],
        "report_sha256": report_hash,
        "native_execution_completed": False,
        "primary_control": "exact_query_count",
        "secondary_control": "exact_query_count_and_object_support_size",
        "status": "implemented_and_tested",
    }
    next_action = (
        f"Retry after {retry_after}. When GPU7 has capacity, run the frozen M95 "
        "native capture, project its rows with "
        "scripts/referent_native_expression_producer_20260919.py, pass the "
        "projection through scripts/referent_object_rank_capture_20260919.py "
        "and scripts/referent_target_rank_evaluator_20260919.py, then run "
        "scripts/referent_query_coverage_control_20260919.py. Reject any "
        "expression with missing candidate, query, support-size, or seed "
        "coverage without imputation. If the exact-coverage gate is not met, "
        "do not promote the all-candidate rank contrast; retain the dual-"
        "balanced subset only as a sensitivity diagnostic."
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
        candidate["dual_balance_progress"] = dual_balance_progress
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
    verified_by_id = {
        candidate["id"]: candidate
        for candidate in verified["candidates"]
    }
    for candidate_id in CANDIDATE_IDS:
        candidate = verified_by_id[candidate_id]
        if candidate.get("retry_after") != retry_after:
            raise SystemExit(f"{candidate_id}: retry time was not persisted")
        if candidate.get("dual_balance_progress") != dual_balance_progress:
            raise SystemExit(f"{candidate_id}: dual-balance progress was not persisted")
        if evidence_entry not in candidate.get("evidence", []):
            raise SystemExit(f"{candidate_id}: evidence was not persisted")

    print(
        json.dumps(
            {
                "report": evidence_entry,
                "updated_candidates": CANDIDATE_IDS,
                "m197": report["m197_snapshot_progress"],
                "dual_balance": report["static_research_progress"][
                    "support_balance_control"
                ],
                "cpu_validation": report["cpu_validation"],
                "post_write_validation": "ok",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
