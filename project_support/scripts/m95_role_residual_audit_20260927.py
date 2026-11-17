"""Audit residual negative vector dots after scalar-sign factorization."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "pipeline/reports/m95_role_gradient_scalar_native_20260927.json"
OUTPUT = ROOT / "pipeline/reports/m95_role_residual_audit_20260927.json"
EXPECTED = "cec227e442bcf490f9e6304c242376864b9a27f0590ea15390d71d7acc120fc6"


def main():
    if OUTPUT.exists() or hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError("Native source differs or output exists")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    endpoints = {(r["scene"], r["ann_id"]): r for r in source["rows"]}
    if len(endpoints) != 128:
        raise ValueError("Native expression population incomplete")
    all_residual = []
    seen = set()
    for r in source["role_gradient_rows"]:
        scalar_same = r["scalar_gradients"][0] * r["scalar_gradients"][2] > 0
        if not scalar_same or r["dots"][1] >= 0:
            continue
        key = (r["scene"], r["target_ann"], r["zero_ann"],
               r["instance"], r["fps_position"])
        if key in seen:
            raise ValueError("Duplicate ordered binding")
        seen.add(key)
        target = endpoints[(r["scene"], r["target_ann"])]
        zero = endpoints[(r["scene"], r["zero_ann"])]
        all_residual.append({
            "scene": r["scene"], "target_ann": r["target_ann"],
            "zero_ann": r["zero_ann"], "instance": r["instance"],
            "fps_position": r["fps_position"],
            "target_final_label": r["target_final_label"],
            "target_deployed_iou": target["selected_mask_iou"],
            "target_deployed_instance": target["selected_seed_instance"],
            "zero_deployed_iou": zero["selected_mask_iou"],
            "zero_deployed_instance": zero["selected_seed_instance"],
        })
    by_scene = defaultdict(list)
    for r in all_residual:
        by_scene[r["scene"]].append(r)
    result = {
        "contract": "m95_role_residual_audit_v1", "admission": False,
        "source_sha256": EXPECTED, "ordered_comparisons": len(all_residual),
        "physical_positions": len({
            (r["scene"], r["instance"], r["fps_position"])
            for r in all_residual}),
        "distinct_target_expressions": len({
            (r["scene"], r["target_ann"]) for r in all_residual}),
        "scenes": len(by_scene),
        "target_deployed_failures": sum(
            r["target_deployed_iou"] <= .5 for r in all_residual),
        "target_deployed_wrong_instance": sum(
            r["target_deployed_instance"] != r["instance"]
            for r in all_residual),
        "scene_counts": {scene: len(rows)
                         for scene, rows in sorted(by_scene.items())},
        "rows": all_residual,
        "limits": "Two-scene observational association only; no new information "
                  "path, randomized control, new-model backward, or efficacy.",
    }
    if len(all_residual) != 13 or len(by_scene) != 2:
        raise ValueError("Residual population differs from scalar audit")
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "ordered_comparisons", "physical_positions", "scenes",
        "distinct_target_expressions", "target_deployed_failures")}))


if __name__ == "__main__":
    main()
