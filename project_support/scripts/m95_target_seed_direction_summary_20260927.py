"""Audit native target-instance seed focal directions by expression and scene."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "pipeline/reports"
SOURCE = REPORT / "m95_target_seed_direction_native_20260927.json"
PREVIOUS = REPORT / "m95_cross_expression_role_1999_20260927.json"
OUTPUT = REPORT / "m95_target_seed_direction_summary_20260927.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUTPUT.exists():
        raise ValueError("Output exists")
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    prior = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    rows = data["rows"]
    census = data["target_seed_direction_rows"]
    previous = {(r["scene"], r["ann_id"]): r for r in prior["rows"]}
    if (len(rows) != len(census) or len(rows) != 128
            or data["checkpoint_sha256"] != prior["checkpoint_sha256"]
            or data["population_manifest_sha256"] !=
            prior["population_manifest_sha256"]):
        raise ValueError("Native frozen manifest/checkpoint differs")
    by_scene = defaultdict(list)
    per_expression = []
    for row, item in zip(rows, census):
        key = row["scene"], row["ann_id"]
        old = previous.pop(key)
        if (row["ann_id"] != item["ann_id"]
                or item["instance"] not in row["target_instances"]
                or row["batch_input_sha256"] != old["batch_input_sha256"]
                or row["selected_seed"] != old["selected_seed"]
                or item["target_seed_count"] != len(item["seeds"])):
            raise ValueError("Expression/physical binding differs")
        valid = [r for r in item["seeds"] if 0 < r[1] <= 1]
        if len(valid) != len(item["seeds"]):
            raise ValueError("Physical target seed has non-positive label")
        outcome = {
            "scene": row["scene"], "ann_id": row["ann_id"],
            "deployed_failure": row["selected_mask_iou"] <= .5,
            "target_seeds": len(valid),
            "suppressive": sum(r[3] > 0 for r in valid),
            "attractive": sum(r[3] < 0 for r in valid),
            "zero_derivative": sum(r[3] == 0 for r in valid),
            "soft_labels": sum(r[1] < 1 for r in valid),
        }
        by_scene[row["scene"]].append(outcome)
        per_expression.append(outcome)
    if previous:
        raise ValueError("Frozen expressions missing")
    failed = [r for r in per_expression if r["deployed_failure"]]
    passed = [r for r in per_expression if not r["deployed_failure"]]
    result = {
        "contract": "m95_target_seed_direction_summary_v1",
        "admission": False, "source_sha256": digest(SOURCE),
        "previous_sha256": digest(PREVIOUS),
        "expressions": len(per_expression), "scenes": len(by_scene),
        "target_seeds": sum(r["target_seeds"] for r in per_expression),
        "zero_target_seed_expressions": sum(
            r["target_seeds"] == 0 for r in per_expression),
        "suppressive_target_seeds": sum(
            r["suppressive"] for r in per_expression),
        "attractive_target_seeds": sum(
            r["attractive"] for r in per_expression),
        "suppressive_expressions": sum(
            r["suppressive"] > 0 for r in per_expression),
        "failures": len(failed), "successes": len(passed),
        "failure_suppressive_expressions": sum(
            r["suppressive"] > 0 for r in failed),
        "success_suppressive_expressions": sum(
            r["suppressive"] > 0 for r in passed),
        "failure_target_seed_absent": sum(
            r["target_seeds"] == 0 for r in failed),
        "success_target_seed_absent": sum(
            r["target_seeds"] == 0 for r in passed),
        "scene_details": [
            {"scene": scene, "expressions": len(items),
             "failures": sum(r["deployed_failure"] for r in items),
             "suppressive_expressions": sum(
                 r["suppressive"] > 0 for r in items),
             "target_seed_absent": sum(r["target_seeds"] == 0 for r in items)}
            for scene, items in sorted(by_scene.items())
        ],
        "limits": "Fixed 32-scene TRAIN diagnosis only. Soft-label positive "
                  "gradient is not automatically harmful; no intervention, "
                  "new-model backward, resources, efficacy or admission.",
    }
    if len(by_scene) != 32:
        raise ValueError("Scene denominator differs")
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "target_seeds", "suppressive_target_seeds",
        "suppressive_expressions", "failure_suppressive_expressions",
        "success_suppressive_expressions", "zero_target_seed_expressions")}))


if __name__ == "__main__":
    main()
