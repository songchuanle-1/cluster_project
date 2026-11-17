"""Persist this event's static control correction without changing the queue."""
import json
from datetime import datetime
from pathlib import Path

from referent_object_rank_capture_20260919 import file_sha256

ROOT = Path(__file__).resolve().parents[1]
REPORT = "pipeline/reports/control_semantics_20260919-1814.json"
DECISION = "pipeline/decisions/20260919-181314_route_change.md"


def main():
    context = json.loads((ROOT / "pipeline/headless/.tick_context.json").read_text("utf-8"))
    work_path = ROOT / "pipeline/research_work.json"
    work = json.loads(work_path.read_text("utf-8"))
    now = datetime.now().astimezone().isoformat()
    retry = "2026-09-19T19:07:00+08:00"
    paths = [
        "scripts/referent_native_expression_producer_20260919.py",
        "scripts/test_referent_native_expression_producer_20260919.py",
        "scripts/referent_native_chain_selftest_20260919.py",
        "scripts/native_support_capture_v2_20260916.py",
        "pipeline/reports/referent_native_chain_selftest_20260919-1812.json",
        "pipeline/bugfixes/bugfix_20260919-1812.md",
        DECISION,
        "scripts/persist_control_semantics_20260919.py",
    ]
    evidence = [{"path": path, "sha256": file_sha256(ROOT / path)} for path in paths]
    changed = {item["path"]: item["sha256"] for item in evidence}
    previous_hashes = []
    due = set(context["research_work"]["due_ids"])
    blocker = (
        "Live server-6 GPU7 query on 2026-09-19 18:08 Asia/Shanghai found "
        "M197 pid1134192 (19956 MiB) and foreign pid3827570 (42488 MiB), "
        "at the two-process cap; 18597 MiB free. Do not launch native capture."
    )
    next_action = (
        "First complete CPU control-source derivation: specify a target-independent "
        "negative-control score and its source, matched-target invariance test, "
        "degeneracy and rejection rules; version the capture producer only after "
        "that review. Existing frozen capture has target IoU only and cannot "
        "satisfy paired rank/control semantics. Do not substitute a quality head "
        "or relabel oracle IoU. Recheck GPU7 after " + retry + "; native execution "
        "requires fewer than two processes and enough measured memory, plus the "
        "corrected producer contract. Then validate FPS composition, identity, "
        "coverage gate and score provenance without imputation; no admission yet."
    )
    for candidate in work["candidates"]:
        if candidate["id"] not in due:
            continue
        for item in candidate["evidence"]:
            replacement = changed.get(item["path"])
            if replacement and replacement != item["sha256"]:
                previous_hashes.append({
                    "candidate_id": candidate["id"], "path": item["path"],
                    "previous_sha256": item["sha256"], "current_sha256": replacement,
                })
                item["sha256"] = replacement
        candidate.update(
            stage="implementation" if candidate["id"] == "referent-causality-audit" else "blocked",
            blocker=blocker, retry_after=retry,
            unblock_condition=(
                "GPU7 fewer than two processes with sufficient measured memory; "
                "paired rank/control also requires source-verified target-independent scores."
            ),
            next_action=next_action,
            latest_progress=now + ": rejected target-IoU/objectness alias; 69 static tests "
            "and six synthetic chain checks passed; native control remains unavailable.",
        )
        candidate["control_semantics_progress"] = {
            "timestamp": now, "report": REPORT, "native_execution_completed": False,
            "scientific_validation_complete": False, "tests_passed": 69,
            "alternatives_attempted": (
                "Inspected native producer source, reproduced target-dependent control, "
                "removed fallback, checked 732 axis reorderings, verified live training steps."
            ),
        }
    report = {
        "schema_version": 1, "generated_at": now,
        "scope": "CPU-only shared diagnostic correction, not mechanism admission",
        "finding": "Native ious measure query masks against designated target; not objectness.",
        "gpu_observation": {
            "server": "server-6", "gpu": 7, "process_count": 2,
            "total_mib": 81559, "used_mib": 62483, "free_mib": 18597,
            "utilization_percent": 100,
            "processes": [
                {"pid": 1134192, "memory_mib": 19956, "role": "M197"},
                {"pid": 3827570, "memory_mib": 42488, "role": "foreign"},
            ],
        },
        "training_progress": {
            "source": "bounded live tail from exact /proc/1134192/fd/1 log",
            "log": "/data3/songcl/Project/Cluster_project/Cluster/logs/"
            "train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pirs_20260916_122540.log",
            "epoch": 23, "first_visible_step": 3717, "last_visible_step": 3754,
            "steps_per_epoch": 4686, "best_miou_preflight": 0.4918,
            "limitation": "Recent sequential steps in one bounded tail, not two timed samples.",
        },
        "validation": {
            "pre_fix_tests": 22, "pre_fix_failures_including_subtests": 9,
            "focused_tests_passed": 69, "synthetic_chain_checks": 6,
            "support_permutations": 720, "fps_permutations": 6, "query_permutations": 6,
        },
        "limitations": [
            "Synthetic objectness values validate code only, not native availability.",
            "Semantics declaration is not proof of score independence.",
            "Prior synthetic permutation calibration is not native control specificity.",
            "Separate seed-inside-ANY-instance intervention is unaffected by this adapter bug.",
        ],
        "source_evidence_refresh": previous_hashes, "evidence": evidence,
        "next_action": next_action, "blocker": blocker, "retry_after": retry,
        "native_execution_completed": False, "queue_changed": False,
    }
    (ROOT / REPORT).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report_entry = {"path": REPORT, "sha256": file_sha256(ROOT / REPORT)}
    for candidate in work["candidates"]:
        if candidate["id"] not in due:
            continue
        by_path = {item["path"]: item for item in candidate["evidence"]}
        for item in evidence + [report_entry]:
            by_path[item["path"]] = item
        candidate["evidence"] = list(by_path.values())
        candidate["control_semantics_progress"]["report_sha256"] = report_entry["sha256"]
    work_path.write_text(json.dumps(work, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"report": report_entry, "resumed_due_ids": sorted(due)}, indent=2))


if __name__ == "__main__":
    main()
