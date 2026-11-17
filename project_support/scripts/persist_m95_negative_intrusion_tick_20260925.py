"""Persist the M95 negative-intrusion rejection and design-cycle stop."""
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK_PATH = ROOT / "pipeline" / "research_work.json"
CANDIDATE_ID = "referent-supervision-axis"
SEED_CANDIDATE_ID = "seed-mask-binding-consistency"
STOP_REASONS = {
    "tick_deadline_near",
    "external_resource_blocked",
    "goal_phase_hold",
}


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evidence(path):
    artifact = ROOT / path
    if not artifact.is_file():
        raise ValueError("Missing evidence artifact: %s" % path)
    return {"path": path, "sha256": file_sha256(artifact)}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stop-reason", choices=sorted(STOP_REASONS), required=True)
    parser.add_argument("--timestamp", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    work = json.loads(WORK_PATH.read_text(encoding="utf-8"))
    candidate = next(
        item for item in work["candidates"] if item.get("id") == CANDIDATE_ID
    )
    artifacts = [
        evidence("pipeline/reports/m95_negative_intrusion_partition_20260925-0731.json"),
        evidence("pipeline/analyses/M95-negative-intrusion-partition_20260925-0731.md"),
        evidence("scripts/m95_negative_intrusion_partition_20260925.py"),
        evidence("scripts/test_m95_negative_intrusion_partition_20260925.py"),
        evidence("pipeline/decisions/20260925-073142_route_change.md"),
    ]
    seed_artifacts = [
        evidence("pipeline/reports/m95_seed_mask_binding_partition_20260925-0745.json"),
        evidence("pipeline/analyses/M95-seed-mask-binding-partition_20260925-0745.md"),
        evidence("scripts/m95_seed_mask_binding_partition_20260925.py"),
        evidence("scripts/test_m95_seed_mask_binding_partition_20260925.py"),
        evidence("pipeline/decisions/20260925-073920_route_change.md"),
    ]
    existing = {entry["path"] for entry in candidate.get("evidence", [])}
    for entry in artifacts:
        if entry["path"] not in existing:
            candidate.setdefault("evidence", []).append(entry)

    candidate.update({
        "stage": "rejected",
        "status": "rejected_native_negative_query_intrusion",
        "blocker": None,
        "resume_condition": (
            "Resume only with a new independently motivated causal unit that "
            "injects identifying evidence not already covered by the closed "
            "referent classification, ranking, PIRS, mask-aware matching, "
            "relation, or multi-scale context families."
        ),
        "next_action": (
            "Do not reopen native-negative query intrusion as a new candidate. "
            "The exact 49-row partition is a closed selector/classification "
            "restatement; no model, queue, training, or launch mutation."
        ),
        "negative_intrusion_progress_20260925": {
            "timestamp": args.timestamp,
            "stage": "rejected",
            "report": artifacts[0],
            "analysis": artifacts[1],
            "checker": artifacts[2],
            "test": artifacts[3],
            "decision": artifacts[4],
            "native_negative_deployed_mismatches": 49,
            "wrong_instance_iou_above_half": 32,
            "target_iou_above_half_false_negative": 4,
            "neither_target_nor_wrong_instance": 13,
            "best_positive_seed_inside_target": 42,
            "selected_seed_inside_target": 0,
            "median_best_positive_score_rank": 4,
            "scene_balanced_positive_minus_selected_iou": 0.5050258677528829,
            "local_tests_passed": 10,
            "remote_tests_passed": 10,
            "independence_boundary": (
                "The non-oracle intervention is the existing indis ranking; "
                "all alternatives duplicate closed selector, quality-target, "
                "listwise, exclusivity, PIRS, or mask-aware matching routes."
            ),
            "native_execution_completed": False,
            "admission": False,
        },
    })

    seed_candidate = next(
        (item for item in work["candidates"]
         if item.get("id") == SEED_CANDIDATE_ID),
        None,
    )
    if seed_candidate is None:
        seed_candidate = {"id": SEED_CANDIDATE_ID}
        work["candidates"].append(seed_candidate)
    seed_candidate.update({
        "stage": "rejected",
        "status": "rejected_non_invariant_seed_mask_binding",
        "latest_progress": (
            "%s: Only 354/32768 query masks contain their own sampled seed; "
            "48/49 deployed native-negative selections exclude their seed, "
            "but only 1/49 places the seed on the selected wrong instance and "
            "0/49 on the target. Seed membership is not an invariant or an "
            "enriched failure cause." % args.timestamp
        ),
        "next_action": (
            "Do not implement a seed-membership or seed-mask consistency loss. "
            "The evidence does not support it and target-seeded positives are "
            "still outranked, which remains inside the closed selector route."
        ),
        "blocker": None,
        "resume_condition": (
            "Reopen only with new evidence that query seeds are intended mask "
            "anchors and that their violation causally predicts target failure."
        ),
        "evidence": seed_artifacts,
        "admission": False,
        "seed_mask_progress_20260925": {
            "timestamp": args.timestamp,
            "report": seed_artifacts[0],
            "analysis": seed_artifacts[1],
            "checker": seed_artifacts[2],
            "test": seed_artifacts[3],
            "decision": seed_artifacts[4],
            "queries": 32768,
            "seed_in_its_mask": 354,
            "selected_native_negative_rows": 49,
            "selected_mask_excludes_own_seed": 48,
            "selected_seed_on_wrong_instance": 1,
            "selected_seed_on_target": 0,
            "selected_seed_on_other_instance": 36,
            "selected_seed_background": 12,
            "local_tests_passed": 7,
            "remote_tests_passed": 7,
            "native_execution_completed": False,
            "admission": False,
        },
    })

    work["updated_at"] = args.timestamp
    work["design_cycle"] = {
        "timestamp": args.timestamp,
        "stop_reason": args.stop_reason,
        "deferred_reason": (
            "Native-negative query intrusion duplicates closed referent "
            "classification/ranking routes, and seed-mask consistency is not "
            "an invariant or enriched failure cause."
        ),
        "attempted_ids": [CANDIDATE_ID, SEED_CANDIDATE_ID],
        "evidence": artifacts + seed_artifacts,
        "resume_condition": (
            "Next design tick: derive an independent mechanism outside closed "
            "selector, ranking, identity, PIRS, mask-aware matching, relation, "
            "seed-mask binding, and multi-scale context families, with a "
            "concrete executable native diagnostic before admission."
        ),
        "blocker": None,
    }
    WORK_PATH.write_text(
        json.dumps(work, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "candidate": CANDIDATE_ID,
                "seed_candidate": SEED_CANDIDATE_ID,
                "stop_reason": args.stop_reason,
                "timestamp": args.timestamp,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
