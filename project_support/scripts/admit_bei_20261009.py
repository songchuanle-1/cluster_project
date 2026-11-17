"""Persist a substantively reviewed BEI receipt under the owning lease."""
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
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    owner = foreground_tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == args.token and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    audit_path = "pipeline/reports/bei_admission_audit_20261009-1042.json"
    audit = foreground_tick.load(ROOT / audit_path)
    assert all(audit["gates"].values())
    commit = closure.git(ROOT / "Cluster", "rev-parse", "HEAD")
    assert commit == audit["code_commit"]
    assert closure.digest(ROOT / "pipeline/goal.json") == audit["goal_sha256"]
    native = "pipeline/reports/bei_sorted_native_20261009-1030.json"
    batch2 = "pipeline/reports/bei_sorted_batch2_20261009-1030.json"
    review = "pipeline/reviews/bei_constraints_independence_20261009.md"
    design = "pipeline/designs/exp_design_20261009-1032.md"
    prereg = "pipeline/designs/m95_oriented_boundary_prereg_20261009-1023.md"
    operator = "pipeline/reports/bei_contracts_20261009-1029.json"
    receipt_relative = "pipeline/admissions/M199-BEI.json"
    assert not (ROOT / receipt_relative).exists()
    gates = {
        "diagnosis": {"passed": True, "evidence": [
            evidence(prereg), evidence("pipeline/reports/m95_boundary_incidence_20261009-1014.json")]},
        "controls": {"passed": True, "evidence": [
            evidence(native), evidence(batch2), evidence(operator)]},
        "native_backward": {"passed": True, "evidence": [evidence(native), evidence(batch2)]},
        "resources": {"passed": True, "evidence": [evidence(audit_path)]},
        "independence": {"passed": True, "evidence": [evidence(audit_path), evidence(review)]},
        "constraints": {"passed": True, "evidence": [
            evidence(review), evidence(design), evidence(audit_path)]}}
    receipt = {
        "id": "M199-BEI", "candidate_id": "m95-native-mask-boundary-incidence",
        "config": audit["config"], "code_commit": commit,
        "goal_sha256": audit["goal_sha256"], "decision": evidence(args.decision),
        "gates": gates, "created_at": datetime.now().astimezone().isoformat(),
        "evaluation_plan": {
            "primary": "Original ScanRefer VAL mIoU", "baseline": 0.4894, "champion": 0.5020,
            "clustering_unit": "scene", "noise_floor": "unknown",
            "subgroups": ["native cut versus no-cut", "multiple same-category versus unique"],
            "material_subgroup_harm": "0.002 decline with scene uncertainty; inadequate data inconclusive",
            "memory_retention": "If peak memory+15%, require trained mIoU gain>=0.003 to retain",
            "design": evidence(design), "seed": 1999, "epochs": 50, "max_iters": 70},
        "literature_limit": "Pairwise likelihood and affinity are prior art; exhaustive novelty unverified.",
        "trained_efficacy_known": False}
    lock = pipeline_monitor.acquire_lock(str(ROOT))
    assert lock is not None, "Canonical queue lock busy"
    try:
        queue = pipeline_monitor.load_queue(str(ROOT))
        assert not any(row["id"] == "M199-BEI" for rows in queue["gpu_queues"].values()
                       for row in rows)
        active = sum(row.get("status") in ("waiting", "claiming", "running")
                     for row in queue["gpu_queues"]["server-6"])
        assert active < 2
        with (ROOT / receipt_relative).open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, indent=2, allow_nan=False)
        task = {
            "id": "M199-BEI", "config": audit["config"], "status": "waiting", "gpu": 7,
            "label": "M199 Directed native boundary incidence; seed1999; frozen schedule",
            "code_commit": commit, "admission_receipt": receipt_relative,
            "candidate_id": receipt["candidate_id"], "patience": queue["patience"]}
        closure.admission(ROOT, task)
        queue["gpu_queues"]["server-6"].append(task)
        pipeline_monitor.save_queue(str(ROOT), queue)
        work = foreground_tick.load(ROOT / "pipeline/research_work.json")
        candidate = next(row for row in work["candidates"] if row["id"] == receipt["candidate_id"])
        candidate.update(
            stage="admission", experiment_id=task["id"],
            next_action="Gated dispatch; require increasing native Train steps. Efficacy unknown.",
            latest_progress="Six reviewed gates pass, including original physical batch2. One receipt and one waiting task.")
        candidate["evidence"].extend(evidence(path) for path in [
            prereg, "pipeline/reviews/motivation_review_20261009-1032.md", design, review,
            "pipeline/reports/bei_native_20261009-1029.json", native, batch2, operator,
            audit_path, receipt_relative])
        work.pop("design_cycle", None)
        foreground_tick.save(ROOT / "pipeline/research_work.json", work)
    finally:
        lock.close()
    print(json.dumps({"admitted": "M199-BEI", "code_commit": commit, "training_started": False}))


if __name__ == "__main__":
    main()
