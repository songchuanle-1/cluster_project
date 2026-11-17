"""Persist the bounded native-projection event with hash-addressed evidence."""
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

from referent_object_rank_capture_20260919 import file_sha256


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    now = datetime.now().astimezone()
    retry = now.replace(minute=7, second=0, microsecond=0) + timedelta(hours=1)
    context = json.loads(
        (root / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8")
    )
    due = set(context["research_work"]["due_ids"])
    selftest = "pipeline/reports/referent_native_chain_selftest_20260919-1715.json"
    report_path = "pipeline/reports/native_projection_fix_20260919-1715.json"
    changed = [
        "scripts/referent_native_expression_producer_20260919.py",
        "scripts/test_referent_native_expression_producer_20260919.py",
        "scripts/referent_native_chain_selftest_20260919.py",
    ]
    paths = changed + [
        "scripts/native_support_capture_v2_20260916.py",
        selftest,
        "pipeline/bugfixes/bugfix_20260919-1715.md",
        args.decision,
    ]
    evidence = [{"path": p, "sha256": file_sha256(root / p)} for p in paths]
    work_path = root / "pipeline/research_work.json"
    work = json.loads(work_path.read_text(encoding="utf-8"))
    replacements = []
    current_hashes = {e["path"]: e["sha256"] for e in evidence}
    for candidate in work["candidates"]:
        for entry in candidate.get("evidence", []):
            if entry["path"] in changed:
                current = current_hashes[entry["path"]]
                if entry["sha256"] != current:
                    replacements.append({
                        "candidate_id": candidate["id"],
                        "path": entry["path"],
                        "previous_sha256": entry["sha256"],
                        "current_sha256": current,
                    })
                    entry["sha256"] = current
    blocker = (
        "The 2026-09-19 17:07 event tick live GPU7 query found M197-PIRS "
        "pid1134192 (19956 MiB) and foreign pid3827570 (42488 MiB), "
        "at the two-process cap with 18597 MiB free. Native capture cannot "
        "launch without exceeding the allocation."
    )
    next_action = (
        f"Retry after {retry.isoformat()}. If GPU7 has fewer than two "
        "processes and sufficient measured memory, execute frozen M95 TRAIN "
        "capture; validate producer/binding and compose fps_superpoints with "
        "sampled_seed_indices using the corrected adapter. Build rank capture "
        "and evaluate coverage plus calibrated permutation control. Reject "
        "missing or malformed identities, FPS, query, candidate, mask, support "
        "or cost evidence without imputation. Do not promote the primary rank "
        "contrast unless the exact-coverage gate passes."
    )
    report = {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "scope": "CPU static diagnostic correction; no native forward or efficacy claim",
        "gpu_observation": {
            "source": "one targeted SSH query during this event tick",
            "remote_timestamp_raw": "2026/09/19 09:11:40.239",
            "remote_clock_timezone_verified": False,
            "server": "server-6",
            "gpu": 7,
            "process_count": 2,
            "memory_total_mib": 81559,
            "memory_used_mib": 62483,
            "memory_free_mib": 18597,
            "utilization_percent": 85,
            "processes": [
                {"pid": 1134192, "memory_mib": 19956, "role": "M197-PIRS"},
                {"pid": 3827570, "memory_mib": 42488, "role": "foreign"},
            ],
        },
        "training_progress": {
            "source": "completed preflight; no new launch verification",
            "epoch": 23, "total_epochs": 50, "best_miou": 0.4918,
            "no_improve": 0,
            "limitation": "Live PID/config confirmed; intra-tick step advance not measured.",
        },
        "reproduction": {
            "fps_superpoints": [4, 0, 2],
            "sampled_seed_indices": [0, 1, 2],
            "before_query_seed_indices": [0, 1, 2],
            "after_query_seed_indices": [4, 0, 2],
            "lossy_id_examples_previously_accepted": ["ann_id=10.9", "dataset_index=False"],
            "pre_fix_tests_run": 17,
            "pre_fix_failures_including_subtests": 47,
        },
        "validation": {
            "focused_tests_passed": 65,
            "focused_tests_failed": 0,
            "synthetic_chain_checks_passed": 6,
            "selftest": selftest,
            "native_execution_completed": False,
        },
        "historical_evidence_limitation": (
            "Previous synthetic chain used identity FPS and did not test "
            "native FPS-to-superpoint composition; retained reports are historical."
        ),
        "source_evidence_refresh": replacements,
        "evidence": evidence,
        "blocker": blocker,
        "retry_after": retry.isoformat(),
        "next_action": next_action,
        "native_capture_launched": False,
        "queue_changed": False,
    }
    (root / report_path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report_entry = {"path": report_path, "sha256": file_sha256(root / report_path)}
    for candidate in work["candidates"]:
        if candidate["id"] not in due:
            continue
        candidate.update(
            stage="blocked", blocker=blocker, retry_after=retry.isoformat(),
            unblock_condition=(
                "GPU7 has fewer than two processes and sufficient measured "
                "free memory; do not interrupt either existing process."
            ),
            next_action=next_action,
            latest_progress=(
                now.isoformat() + ": corrected native FPS seed composition and "
                "lossy physical identity coercion; 65 static tests and six "
                "non-identity-FPS integration checks passed. GPU capture blocked."
            ),
            native_projection_fix_progress={
                "timestamp": now.isoformat(),
                "report": report_path,
                "report_sha256": report_entry["sha256"],
                "native_execution_completed": False,
                "tests_passed": 65,
                "limitation": "Shared diagnostic correction, not candidate-specific native validation.",
            },
        )
        by_path = {e["path"]: e for e in candidate["evidence"]}
        for entry in evidence + [report_entry]:
            by_path[entry["path"]] = dict(entry)
        candidate["evidence"] = list(by_path.values())
    work["last_event_tick"] = now.isoformat()
    work_path.write_text(json.dumps(work, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": report_entry, "due_candidates_updated": len(due),
        "source_evidence_refreshed": len(replacements), "retry_after": retry.isoformat(),
    }, indent=2))


if __name__ == "__main__":
    main()
