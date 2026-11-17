"""Frozen role-gradient/outcome join, deduplicated by physical seed."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "pipeline/reports/m95_target_seed_size_native_20260927.json"
ROLES = ROOT / "pipeline/reports/m95_role_gradient_native_20260927.json"
SEEDS_SHA = "97d95b265b3e1a79e65f01748946f9eab9ff81d90efcfc05365894ddce58106c"
ROLES_SHA = "b01b4f0423ec08177cd8d1c4544f5615f1bd8b0abe80b31e8cb17cbe377b50a0"


def analyze(seeds, roles):
    expressions = {}
    for row in seeds["rows"]:
        key = (row["scene"], row["ann_id"])
        if key in expressions:
            raise ValueError("Duplicate expression binding")
        expressions[key] = row["selected_mask_iou"] <= .5
    if len(expressions) != 128:
        raise ValueError("Frozen expression cohort changed")
    physical = defaultdict(list)
    for row in roles["role_gradient_rows"]:
        key = (row["scene"], row["target_ann"])
        if key not in expressions:
            raise ValueError("Gradient target expression absent")
        if min(row["norms"]) <= 0 or not row["target_protected"]:
            raise ValueError("Gradient/positive contract changed")
        physical[(row["scene"], row["instance"], row["target_ann"],
                  row["fps_position"])].append(row)
    if len(physical) != 139 or sum(map(len, physical.values())) != 266:
        raise ValueError("Physical cohort changed")
    by_expr = defaultdict(list)
    for (scene, _, ann, _), repeats in physical.items():
        if len(repeats) not in (1, 2):
            raise ValueError("Unexpected zero-role multiplicity")
        by_expr[(scene, ann)].append((
            sum(r["dots"][1] < 0 for r in repeats) / len(repeats),
            sum(r["dots"][0] < 0 for r in repeats) / len(repeats)))
    by_scene = defaultdict(lambda: [[], []])
    for key, positions in by_expr.items():
        by_scene[key[0]][int(expressions[key])].append((
            sum(p[0] for p in positions) / len(positions),
            sum(p[1] for p in positions) / len(positions)))
    paired = []
    for scene, (success, failure) in sorted(by_scene.items()):
        if not success or not failure:
            continue
        paired.append({
            "scene": scene, "success_expressions": len(success),
            "failure_expressions": len(failure),
            "zero_failure_minus_success": (
                sum(x[0] for x in failure) / len(failure) -
                sum(x[0] for x in success) / len(success)),
            "context_failure_minus_success": (
                sum(x[1] for x in failure) / len(failure) -
                sum(x[1] for x in success) / len(success)),
        })
    return {
        "contract": "m95_target_zero_failure_v1",
        "admission": False,
        "seed_source_sha256": SEEDS_SHA,
        "role_source_sha256": ROLES_SHA,
        "physical_positions": len(physical),
        "target_expressions": len(by_expr),
        "paired_scenes": len(paired),
        "zero_higher_failure_scenes": sum(
            r["zero_failure_minus_success"] > 0 for r in paired),
        "zero_lower_failure_scenes": sum(
            r["zero_failure_minus_success"] < 0 for r in paired),
        "zero_equal_scenes": sum(
            r["zero_failure_minus_success"] == 0 for r in paired),
        "context_higher_failure_scenes": sum(
            r["context_failure_minus_success"] > 0 for r in paired),
        "detail": paired,
        "limits": "Frozen TRAIN association only; generic contrast/PCGrad "
                  "are not independent methods and no causal efficacy follows.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or any(
            hashlib.sha256(p.read_bytes()).hexdigest() != expected for p, expected
            in ((SEEDS, SEEDS_SHA), (ROLES, ROLES_SHA))):
        raise ValueError("Output exists or frozen source changed")
    result = analyze(json.loads(SEEDS.read_text(encoding="utf-8")),
                     json.loads(ROLES.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "target_expressions", "paired_scenes", "zero_higher_failure_scenes",
        "zero_lower_failure_scenes", "zero_equal_scenes",
        "context_higher_failure_scenes")}))


if __name__ == "__main__":
    main()
