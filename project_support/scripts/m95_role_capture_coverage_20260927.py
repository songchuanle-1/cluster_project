"""Audit selection of frozen M95 role-gradient capture into target expressions."""
import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "pipeline/reports/m95_target_seed_size_native_20260927.json"
ROLE = ROOT / "pipeline/reports/m95_role_gradient_native_20260927.json"
SEED_SHA = "97d95b265b3e1a79e65f01748946f9eab9ff81d90efcfc05365894ddce58106c"
ROLE_SHA = "b01b4f0423ec08177cd8d1c4544f5615f1bd8b0abe80b31e8cb17cbe377b50a0"


def audit(seed, role):
    rows = {}
    for row in seed["rows"]:
        key = (row["scene"], row["ann_id"])
        if key in rows:
            raise ValueError("Duplicate target expression")
        rows[key] = row
    if len(rows) != 128:
        raise ValueError("Frozen cohort changed")
    covered = set()
    for row in role["role_gradient_rows"]:
        key = (row["scene"], row["target_ann"])
        if key not in rows:
            raise ValueError("Unbound role target")
        covered.add(key)
    if len(covered) != 20:
        raise ValueError("Frozen role coverage changed")
    arms = defaultdict(list)
    scenes = defaultdict(lambda: {True: [], False: []})
    for key, row in rows.items():
        failure = row["selected_mask_iou"] <= 0.5
        arm = key in covered
        # Target size is bound independently by the native direction census.
        arms[arm].append(failure)
        scenes[key[0]][arm].append(failure)
    direction = seed["target_seed_direction_rows"]
    if len(direction) != len(seed["rows"]) or any(
        a["ann_id"] != b["ann_id"] for a, b in zip(seed["rows"], direction)
    ):
        raise ValueError("Target-size row bindings changed")
    sizes = {(a["scene"], a["ann_id"]): b["physical_target_superpoints"]
             for a, b in zip(seed["rows"], direction)}
    paired = []
    for scene, groups in sorted(scenes.items()):
        if groups[True] and groups[False]:
            paired.append({
                "scene": scene,
                "covered_count": len(groups[True]),
                "uncovered_count": len(groups[False]),
                "failure_fraction_difference": (
                    sum(groups[True]) / len(groups[True])
                    - sum(groups[False]) / len(groups[False])),
            })
    return {
        "contract": "m95_role_capture_coverage_v1",
        "admission": False,
        "seed_sha256": SEED_SHA,
        "role_sha256": ROLE_SHA,
        "arms": {
            label: {
                "expressions": len(arms[arm]),
                "scenes": len({scene for scene, ann in rows
                               if ((scene, ann) in covered) == arm}),
                "failures": sum(arms[arm]),
                "median_target_superpoints": statistics.median(
                    sizes[key] for key in rows if (key in covered) == arm),
            }
            for label, arm in (("covered", True), ("uncovered", False))
        },
        "paired_scenes": paired,
        "limits": "TRAIN selection diagnostic; no causal effect, efficacy or admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output already exists")
    for path, sha in ((SEED, SEED_SHA), (ROLE, ROLE_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise ValueError("Frozen source changed")
    result = audit(json.loads(SEED.read_text(encoding="utf-8")),
                   json.loads(ROLE.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"arms": result["arms"],
                      "paired_scenes": len(result["paired_scenes"])}))


if __name__ == "__main__":
    main()
