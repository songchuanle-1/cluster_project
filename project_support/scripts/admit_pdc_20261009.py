"""Persist a reviewed PDC receipt and one waiting entry under canonical locks."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
sys.path.insert(0, str(SKILL))
import closure
import foreground_tick
import pipeline_monitor


def evidence(path):
    absolute = ROOT / path
    return {"path": path, "sha256": hashlib.sha256(absolute.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--native", required=True)
    parser.add_argument("--batch2", required=True)
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    owner = foreground_tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    if owner["token"] != args.token or owner["thread_id"] != os.environ["CODEX_THREAD_ID"]:
        raise ValueError("Actual owning foreground lease required")
    audit = foreground_tick.load(ROOT / args.audit)
    batch2 = foreground_tick.load(ROOT / args.batch2)
    if not all(audit["gates"].values()) or not all(
            batch2.get(key) is True for key in
            ("native_backward_pass", "matched_control_pass", "strict_repeat_pass")):
        raise ValueError("All measured gates and multi-scene coverage must pass")
    if batch2["physical_group_batch_size"] != 2:
        raise ValueError("Native coverage does not match existing batch size2")
    commit = closure.git(ROOT / "Cluster", "rev-parse", "HEAD")
    if commit != audit["code_commit"] or closure.digest(ROOT / "pipeline/goal.json") != audit["goal_sha256"]:
        raise ValueError("Audit is not bound to current code and goal")
    review = "pipeline/reviews/pdc_constraints_independence_20261009.md"
    design = "pipeline/designs/exp_design_20261009-0912.md"
    receipt_path = ROOT / "pipeline/admissions/M198-PDC.json"
    if receipt_path.exists():
        raise ValueError("Receipt already exists; reconcile, do not create another")
    gates = {
        "diagnosis": {"passed": True, "evidence": [
            evidence("pipeline/reports/m95_point_detail_population_prereg_20261009.md"),
            evidence("pipeline/reports/m95_point_detail_population_20261009.json")]},
        "controls": {"passed": True, "evidence": [
            evidence(args.native), evidence(args.batch2),
            evidence("pipeline/reports/pdc_operator_verified_20261009.json")]},
        "native_backward": {"passed": True, "evidence": [
            evidence(args.native), evidence(args.batch2)]},
        "resources": {"passed": True, "evidence": [evidence(args.audit)]},
        "independence": {"passed": True, "evidence": [evidence(args.audit), evidence(review)]},
        "constraints": {"passed": True, "evidence": [evidence(review), evidence(design),
                                                    evidence(args.audit)]},
    }
    receipt = {
        "id": "M198-PDC", "candidate_id": "m95-native-point-detail-field",
        "config": audit["config"], "code_commit": commit,
        "goal_sha256": audit["goal_sha256"], "decision": evidence(args.decision),
        "gates": gates, "created_at": datetime.now().astimezone().isoformat(),
        "evaluation_plan": {
            "primary": "ScanRefer VAL mIoU", "baseline": 0.4894, "champion": 0.5020,
            "clustering_unit": "scene", "noise_floor": "unknown",
            "material_subgroup_harm": "0.002 decline with scene uncertainty; inadequate data inconclusive",
            "memory_retention": "If peak memory+15%, require trained mIoU gain>=0.003 to retain",
            "design": evidence(design), "seed": 1999, "epochs": 50, "max_iters": 70,
        },
        "literature_limit": "Point refinement is prior art; exhaustive novelty unverified.",
        "trained_efficacy_known": False,
    }
    lock = pipeline_monitor.acquire_lock(str(ROOT))
    if lock is None:
        raise ValueError("Queue monitor lock is busy; no queue mutation")
    try:
        queue = pipeline_monitor.load_queue(str(ROOT))
        if any(row["id"] == "M198-PDC" for rows in queue["gpu_queues"].values() for row in rows):
            raise ValueError("Experiment already present; reconcile")
        active = sum(row.get("status") in ("waiting", "claiming", "running")
                     for row in queue["gpu_queues"]["server-6"])
        if active >= 2:
            raise ValueError("Authorized two-slot capacity full")
        receipt_path.parent.mkdir(exist_ok=True)
        with receipt_path.open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, indent=2, allow_nan=False)
        task = {
            "id": "M198-PDC", "config": audit["config"], "status": "waiting", "gpu": 7,
            "label": "M198 Mean-constrained native point detail field; seed1999; frozen schedule",
            "code_commit": commit, "admission_receipt": "pipeline/admissions/M198-PDC.json",
            "candidate_id": "m95-native-point-detail-field", "patience": queue["patience"],
        }
        closure.admission(ROOT, task)
        queue["gpu_queues"]["server-6"].append(task)
        pipeline_monitor.save_queue(str(ROOT), queue)
        work = foreground_tick.load(ROOT / "pipeline/research_work.json")
        candidate = next(row for row in work["candidates"] if row["id"] == task["candidate_id"])
        candidate.update(stage="admission", experiment_id=task["id"],
                         next_action="Use the existing gated dispatcher; require increasing native Train steps, not a PID.",
                         latest_progress="Six reviewed gates and actual batch-size2 coverage pass; receipt created, one waiting experiment. Trained efficacy unknown.")
        candidate["evidence"].extend([evidence(args.audit), evidence(args.batch2),
                                      evidence("pipeline/admissions/M198-PDC.json")])
        work.pop("design_cycle", None)
        foreground_tick.save(ROOT / "pipeline/research_work.json", work)
    finally:
        lock.close()
    print(json.dumps({"admitted": "M198-PDC", "code_commit": commit, "training_started": False}))


if __name__ == "__main__":
    main()
