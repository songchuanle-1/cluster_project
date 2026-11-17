"""Group frozen native sampler-gradient contrasts by physical scene target."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "pipeline/reports"
INPUTS = {
    "backward": ("m95_native31_backward_20260928-1131.json",
                 "7d593b940f5a46ce9faefab85e55c1a29491d0b1de57b15c176a7cb971a36b6a"),
    "manifest": ("m95_multiword_capture_manifest_20260928.json",
                 "85e108e8c86d65bcdbdc25061987e0a973fa45b35b00030d0721d359da720040"),
    "roles": ("m95_multiword_population_role_20260928.json",
              "6d3e95e3e29a243152a6f5b7e73b893df96d16e2ee3432c8bf07a3f8418698f7"),
}


def main():
    data = {}
    for name, (filename, expected) in INPUTS.items():
        path = REPORTS / filename
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"{name} input hash changed")
        data[name] = json.loads(path.read_text(encoding="utf-8"))
    rows = data["backward"]["rows"]
    exposed = {
        (r["scene"], int(r["ann_id"])): r
        for r in data["manifest"]["records"] if r["arm"] == "phrase"
    }
    roles = {(r["scene"], int(r["ann_id"])): r
             for r in data["roles"]["rows"]}
    if len(rows) != 11 or len(exposed) != 11:
        raise ValueError("Frozen cohort cardinality changed")
    units = defaultdict(list)
    for row in rows:
        key = row["scene"], int(row["ann_id"])
        if key not in exposed or key not in roles:
            raise ValueError("Unbound native row")
        grad = row["sampler_parameter_backward"]
        if (grad["connected_tensors"] != grad["trainable_tensors"]
                or grad["baseline_grad_l1"] <= 0):
            raise ValueError("Sampler parameter path inactive")
        role = sorted({role for mention in roles[key]["mentions"]
                       for role in mention["roles"]})
        units[(row["scene"], tuple(exposed[key]["target_instances"]))].append({
            "ann_id": key[1],
            "roles": role,
            "treated_minus_placebo_loss":
                row["replay"]["treated_sample_loss"] - row["replay"]["placebo_sample_loss"],
            "treated_minus_placebo_grad_delta":
                grad["treated_delta_l1"] - grad["placebo_delta_l1"],
        })
    if len(units) != 7 or len({key[0] for key in units}) != 2:
        raise ValueError("Frozen independent-unit contract changed")
    grouped = []
    for (scene, target), descriptions in sorted(units.items()):
        grouped.append({
            "scene": scene, "target_instances": target,
            "descriptions": descriptions,
            "mean_loss_contrast": sum(
                d["treated_minus_placebo_loss"] for d in descriptions) / len(descriptions),
            "mean_grad_delta_contrast": sum(
                d["treated_minus_placebo_grad_delta"] for d in descriptions) / len(descriptions),
        })
    scenes = []
    for scene in sorted({unit["scene"] for unit in grouped}):
        selected = [unit for unit in grouped if unit["scene"] == scene]
        scenes.append({
            "scene": scene, "target_units": len(selected),
            "mean_unit_loss_contrast": sum(
                unit["mean_loss_contrast"] for unit in selected) / len(selected),
            "mean_unit_grad_delta_contrast": sum(
                unit["mean_grad_delta_contrast"] for unit in selected) / len(selected),
        })
    output = {
        "contract": "m95_native31_sampler_backward_grouped_v1",
        "admission": False,
        "input_sha256": {key: value[1] for key, value in INPUTS.items()},
        "rows": len(rows), "scene_target_units": len(units),
        "scene_aggregates": scenes,
        "units": grouped,
        "limits": "Two TRAIN scenes only, repeated descriptions and physical geometry. "
                  "Old champion sampler gradients, not a new candidate's backward, "
                  "trained effect, novelty, resource gate or admission.",
    }
    path = REPORTS / "m95_native31_backward_grouped_20260928.json"
    if path.exists():
        raise ValueError("Refusing to overwrite grouped evidence")
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(json.dumps({"rows": len(rows), "units": len(units), "scenes": scenes}))


if __name__ == "__main__":
    main()
