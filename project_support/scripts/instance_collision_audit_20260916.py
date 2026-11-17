"""Static audit of physical-instance collisions in an existing TRAIN capture."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path


def audit(report):
    rows = report["rows"]
    if not rows:
        raise ValueError("Empty capture")
    seen = set()
    groups = defaultdict(list)
    by_scene = defaultdict(list)
    for row in rows:
        key = (row["scene"], tuple(sorted(row["target_ids"])), row["ann_id"])
        if key in seen:
            raise ValueError("Duplicate expression")
        seen.add(key)
        if not row["target_ids"]:
            raise ValueError("Missing target identity")
        if not 0 <= row["before"] <= 1 or not 0 <= row["winner_overlap"] <= 1:
            raise ValueError("Invalid overlap")
        by_scene[row["scene"]].append(row)
        # Physical IDs, not query indices, are the only cross-expression key.
        if row["winner_overlap"] > 0.5 and row["winner_id"] is not None:
            groups[(row["scene"], row["winner_id"])].append(row)
    collisions = []
    collision_keys = set()
    for (scene, winner), members in sorted(groups.items()):
        targets = {tuple(sorted(r["target_ids"])) for r in members}
        if len(targets) < 2:
            continue
        collision_keys.add((scene, winner))
        collisions.append({
            "scene": scene, "winner_id": winner,
            "distinct_target_sets": [list(t) for t in sorted(targets)],
            "n": len(members),
            "correct_identity_present": any(winner in r["target_ids"] for r in members),
            "rows": [{
                "ann_id": r["ann_id"], "target_ids": r["target_ids"],
                "winner_overlap": r["winner_overlap"], "target_iou": r["before"],
                "same_name": r["winner_same_name"], "utterance": r["utterance"],
            } for r in members],
        })
    confident_wrong = [
        r for r in rows if r["before"] <= 0.5 and r["winner_overlap"] > 0.5
        and r["winner_id"] is not None and r["winner_id"] not in r["target_ids"]
    ]
    captured_collision_wrong = [
        r for r in confident_wrong if (r["scene"], r["winner_id"]) in collision_keys
    ]
    paired = []
    for wrong in confident_wrong:
        controls = [
            r for r in groups[(wrong["scene"], wrong["winner_id"])]
            if r["before"] > 0.5 and wrong["winner_id"] in r["target_ids"]
        ]
        if controls:
            paired.append({
                "scene": wrong["scene"], "wrong_ann_id": wrong["ann_id"],
                "wrong_target_ids": wrong["target_ids"], "winner_id": wrong["winner_id"],
                "wrong_utterance": wrong["utterance"],
                "control_ann_ids": [r["ann_id"] for r in controls],
                "control_utterances": [r["utterance"] for r in controls],
            })
    return {
        "summary": {
            "expressions": len(rows), "scenes": len(by_scene),
            "confident_wrong": len(confident_wrong),
            "collision_groups": len(collisions),
            "collision_scenes": len({r["scene"] for r in collisions}),
            "wrong_in_captured_collision": len(captured_collision_wrong),
            "wrong_with_successful_winner_control": len(paired),
        },
        "collision_groups": collisions,
        "matched_description_cases": paired,
        "per_scene": [{
            "scene": scene, "expressions": len(members),
            "confident_wrong": sum(r in confident_wrong for r in members),
            "wrong_in_captured_collision": sum(r in captured_collision_wrong for r in members),
        } for scene, members in sorted(by_scene.items())],
        "limitations": [
            "Static audit of an existing fixed augmented TRAIN capture, not new native execution.",
            "Physical instance identity links descriptions; no cross-forward query-index joins.",
            "Incomplete description sample: no observed collision does not imply no collapse.",
            "Repeated descriptions may correctly select one object; no one-to-one constraint.",
            "No scene geometry, RGB, viewpoint, anchor truth or counterfactual logits here.",
            "Collision is an outcome, not evidence that language was ignored or a relation failed.",
            "Matched cases require same-forward controlled recapture before causal inference.",
            "No efficacy, novelty, generalization or training-admission claim.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.capture.read_text(encoding="utf-8")))
    result["evidence"] = [
        {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in (args.capture, Path(__file__))
    ]
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
