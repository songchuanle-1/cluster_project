"""Frozen role-gradient specificity on selected wrong-context failures."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "pipeline/reports/m95_target_seed_size_native_20260927.json"
ROLE = ROOT / "pipeline/reports/m95_role_gradient_native_20260927.json"
SEED_SHA = "97d95b265b3e1a79e65f01748946f9eab9ff81d90efcfc05365894ddce58106c"
ROLE_SHA = "b01b4f0423ec08177cd8d1c4544f5615f1bd8b0abe80b31e8cb17cbe377b50a0"


def analyze(seed, role):
    if (seed["checkpoint_sha256"] != role["checkpoint_sha256"]
            or seed["population_manifest_sha256"] != role["population_manifest_sha256"]
            or seed["transform_seed"] != role["transform_seed"]
            or not seed["exact_input_fingerprints"]
            or not role["exact_input_fingerprints"]):
        raise ValueError("Capture provenance differs")
    rows = {(r["scene"], r["ann_id"]): r for r in seed["rows"]}
    if len(rows) != len(seed["rows"]) or len(rows) != 128:
        raise ValueError("Seed expression count differs")
    seen = set()
    for r in role["rows"]:
        key = (r["scene"], r["ann_id"])
        if key in seen or key not in rows:
            raise ValueError("Role expression binding differs")
        if (r["batch_input_sha256"] != rows[key]["batch_input_sha256"]
                or abs(r["selected_mask_iou"] -
                       rows[key]["selected_mask_iou"]) > 1e-6):
            raise ValueError("Role expression input/outcome drift")
        seen.add(key)
    if seen != set(rows):
        raise ValueError("Role population incomplete")
    positions = defaultdict(list)
    for r in role["role_gradient_rows"]:
        key = (r["scene"], r["target_ann"])
        if key not in rows or not r["target_protected"] or min(r["norms"]) <= 0:
            raise ValueError("Role gradient binding differs")
        pos = (r["scene"], r["target_ann"], r["instance"], r["fps_position"])
        positions[pos].append(r)
    if len(positions) != 139 or sum(map(len, positions.values())) != 266:
        raise ValueError("Physical gradient count differs")
    expression_positions = defaultdict(list)
    for (scene, ann, _, _), duplicates in positions.items():
        if len(duplicates) not in (1, 2):
            raise ValueError("Unexpected physical repetition")
        expression_positions[(scene, ann)].append((
            sum(r["dots"][0] < 0 for r in duplicates) / len(duplicates),
            sum(r["dots"][1] < 0 for r in duplicates) / len(duplicates)))
    if len(expression_positions) != 20:
        raise ValueError("Covered target count differs")
    groups = defaultdict(list)
    by_scene = defaultdict(lambda: defaultdict(list))
    for key, values in expression_positions.items():
        row = rows[key]
        if row["selected_mask_iou"] > .5:
            group = "success"
        elif row["selected_seed_is_context"]:
            group = "exposed_failure"
        else:
            group = "other_failure"
        context = sum(x[0] for x in values) / len(values)
        zero = sum(x[1] for x in values) / len(values)
        record = {"scene": key[0], "ann_id": key[1],
                  "physical_positions": len(values),
                  "context_negative_fraction": context,
                  "zero_negative_fraction": zero,
                  "context_minus_zero": context-zero}
        groups[group].append(record)
        by_scene[key[0]][group].append(record)
    scene_means = []
    for scene, grouped in sorted(by_scene.items()):
        exposed = grouped["exposed_failure"]
        success = grouped["success"]
        if exposed and success:
            scene_means.append({
                "scene": scene,
                "exposed_count": len(exposed),
                "success_count": len(success),
                "exposed_minus_success_context_minus_zero": (
                    sum(x["context_minus_zero"] for x in exposed)/len(exposed)
                    - sum(x["context_minus_zero"] for x in success)/len(success)),
            })
    return {
        "contract": "m95_exposed_role_gradient_v1",
        "admission": False,
        "seed_sha256": SEED_SHA,
        "role_sha256": ROLE_SHA,
        "groups": {name: {"expressions": len(groups[name]),
                          "scenes": len({x["scene"] for x in groups[name]}),
                          "context_greater": sum(x["context_minus_zero"] > 0 for x in groups[name]),
                          "context_less": sum(x["context_minus_zero"] < 0 for x in groups[name]),
                          "context_equal": sum(x["context_minus_zero"] == 0 for x in groups[name]),
                          "rows": groups[name]}
                   for name in ("exposed_failure", "other_failure", "success")},
        "paired_scenes": scene_means,
        "limits": "Fixed TRAIN gradients are observational; no native new-model backward, matched training control or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or any(
            hashlib.sha256(path.read_bytes()).hexdigest() != sha
            for path, sha in ((SEED, SEED_SHA), (ROLE, ROLE_SHA))):
        raise ValueError("Output exists or frozen source differs")
    result = analyze(json.loads(SEED.read_text(encoding="utf-8")),
                     json.loads(ROLE.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({name: {key: value for key, value in group.items()
                              if key != "rows"}
                      for name, group in result["groups"].items()}))


if __name__ == "__main__":
    main()
