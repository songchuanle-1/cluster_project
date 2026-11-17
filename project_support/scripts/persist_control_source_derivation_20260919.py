"""Persist tested shared diagnostic progress without queue mutation."""
import json
from datetime import datetime
from pathlib import Path
from referent_object_rank_capture_20260919 import file_sha256

ROOT = Path(__file__).resolve().parents[1]
REPORT = "pipeline/reports/control_source_derivation_20260919-1912.json"
MODEL = ("Cluster/framework/model/Quard_model/"
         "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/")


def main():
    context = json.loads((ROOT / "pipeline/headless/.tick_context.json").read_text("utf-8"))
    if context["generated_at"] != "2026-09-19T11:07:10.826946+00:00":
        raise ValueError("Persistence belongs only to the 19:07 event")
    work_path = ROOT / "pipeline/research_work.json"
    work = json.loads(work_path.read_text("utf-8"))
    due = set(context["research_work"]["due_ids"])
    if due - {item["id"] for item in work["candidates"]}:
        raise ValueError("Due candidate missing")
    now = datetime.now().astimezone().isoformat()
    retry = "2026-09-19T20:07:00+08:00"
    paths = [
        "scripts/referent_geometry_control_20260919.py",
        "scripts/test_referent_geometry_control_20260919.py",
        "scripts/persist_control_source_derivation_20260919.py",
        "pipeline/reports/control_source_derivation_20260919-1912.md",
        "pipeline/reports/referent_native_chain_selftest_20260919-1912.json",
        "pipeline/decisions/20260919-191408_route_change.md",
        MODEL + "network.py", MODEL + "dec.py", MODEL + "loss.py",
        MODEL + "sample_model.py",
    ]
    evidence = [{"path": path, "sha256": file_sha256(ROOT / path)} for path in paths]
    blocker = (
        "Live GPU7 check at 2026-09-19 19:09 Asia/Shanghai: M197 pid1134192 "
        "19956 MiB, foreign pid3827570 42488 MiB, two-process cap reached, "
        "18597 MiB free. No native launch. Independent objectness also unresolved."
    )
    next_action = (
        "Continue CPU implementation of a separately versioned geometry-nuisance "
        "capture/evaluation contract using exact criterion input8 coordinates, "
        "input4 labels, input7 FPS, input9 offsets and composed query seeds. "
        "Keep geometry separate from objectness_scores; test coordinate slicing, "
        "physical/hash binding, target swaps, missingness/ties and query-selection "
        "sensitivity before integration. Do not silently modify frozen producer "
        "or relabel geometry as objectness. Recheck GPU7 after " + retry +
        "; fewer than two processes and sufficient memory plus a reviewed "
        "capture contract are required for gated native execution. Preserve "
        "coverage/selection/scene-uncertainty gates; no admission from synthetic tests."
    )
    report = {
        "schema_version": 1, "generated_at": now,
        "scope": "Shared CPU diagnostic derivation, not mechanism admission",
        "finding": "Any-instance membership is constant within each seed-assigned object.",
        "implemented_control": "annotation_assisted_seed_radial_cost_not_objectness_v1",
        "independence": "Conditional on fixed coordinates, labels and query axis only",
        "independent_objectness_resolved": False,
        "validation": {
            "tests_passed": 85, "new_tests": 16, "support_permutations": 720,
            "synthetic_chain_checks": 6,
            "initial_failure": "One exact float assertion differed by about3e-16; "
            "permutation check now compares original computed cost; closed-form "
            "test separately uses assertAlmostEqual.",
        },
        "gpu_observation": {
            "server": "server-6", "gpu": 7, "process_count": 2,
            "total_mib": 81559, "used_mib": 62483, "free_mib": 18597,
            "utilization_percent": 100,
            "processes": [
                {"pid": 1134192, "memory_mib": 19956, "role": "M197"},
                {"pid": 3827570, "memory_mib": 42488, "role": "foreign"},
            ],
        },
        "progress_observation": {
            "source": "One bounded live tail with PID/config and /proc fd1 verified",
            "phase": "Val", "epoch": 23, "first_step": 217, "last_step": 233,
            "total_steps": 363, "best_miou_preflight": 0.4918,
            "previous_tick": "18:08 Train[23/50]3717..3754/4686",
            "limitation": "No completed current validation metric",
        },
        "resumed_due_ids": sorted(due), "evidence": evidence,
        "blocker": blocker, "retry_after": retry, "next_action": next_action,
        "native_execution_completed": False, "scientific_validation_complete": False,
        "queue_changed": False, "native_producer_modified": False,
        "limitations": [
            "Synthetic tests do not establish native efficacy or specificity.",
            "Geometry requires existing annotations and is not deployable objectness.",
            "Language-conditioned seed selection can change gathered geometry costs.",
            "Missing/zero-radius/tied objects are rejected; native prevalence unknown.",
            "Shared evidence is not seven candidate-specific validations.",
        ],
    }
    (ROOT / REPORT).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    entry = {"path": REPORT, "sha256": file_sha256(ROOT / REPORT)}
    for candidate in work["candidates"]:
        if candidate["id"] not in due:
            continue
        by_path = {item["path"]: item for item in candidate["evidence"]}
        for item in evidence + [entry]:
            by_path[item["path"]] = item
        candidate.update(
            stage="implementation" if candidate["id"] == "referent-causality-audit" else "blocked",
            evidence=list(by_path.values()), blocker=blocker, retry_after=retry,
            unblock_condition="GPU7 fewer than two processes with sufficient memory; "
            "paired control needs a separately reviewed, versioned contract.",
            next_action=next_action,
            latest_progress=now + ": rejected degenerate membership rank control; "
            "implemented conditional geometry reference;85 tests and6 synthetic checks "
            "pass, native and candidate-specific validation incomplete.",
            control_source_derivation_progress={
                "timestamp": now, "report": REPORT, "report_sha256": entry["sha256"],
                "tests_passed": 85, "native_execution_completed": False,
                "scientific_validation_complete": False,
                "alternatives_attempted": "Traced native score sources; rejected "
                "target-IoU, quality head, language sampling, max-mask-IoU and "
                "degenerate membership; implemented geometry control; verified live "
                "GPU capacity and validation steps.",
            },
        )
    work_path.write_text(json.dumps(work, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"report": entry, "resumed_due_ids": sorted(due)}, indent=2))


if __name__ == "__main__":
    main()
