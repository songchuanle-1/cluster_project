"""Compare frozen native support placebos on common expressions and scene units."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "pipeline/reports"
INPUTS = {
    "ordered": ("m95_full_train_support_20260928-1149.json",
                "36a95cd8aee1166754a65ea78b278650b8631cc8c9d304128f0f9e888ad5ed5e"),
    "score": ("m95_score_matched_20260928-1153.json",
              "e1fb561a18e4375cd1c5146e4587e78b381eb3ceaa4b3720a0536d90dfc72de2"),
    "roles": ("m95_multiword_population_role_20260928.json",
              "6d3e95e3e29a243152a6f5b7e73b893df96d16e2ee3432c8bf07a3f8418698f7"),
    "physical": ("m95_multiword_population_20260928.json",
                 "325626925578df183ef3f8ffdce2b7cb7f010ccefa87de70db0b4b1353f0d664"),
}


def mean(numbers):
    return sum(numbers) / len(numbers)


def main():
    inputs = {}
    for name, (file, expected) in INPUTS.items():
        path = REPORTS / file
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"{name} evidence hash differs")
        inputs[name] = json.loads(path.read_text(encoding="utf-8"))
    ordered, score = inputs["ordered"], inputs["score"]
    if (ordered["summary"]["cohort"] != 102 or score["summary"]["cohort"] != 102
            or ordered["population_sha256"] != score["population_sha256"]):
        raise ValueError("Full TRAIN cohort differs")
    old = {(r["scene"], r["ann_id"]): r for r in ordered["rows"]}
    new = {(r["scene"], r["ann_id"]): r for r in score["rows"]}
    if len(old) != 102 or old.keys() != new.keys():
        raise ValueError("Native identities differ")
    physical = {(r["scene"], r["ann_id"]): r
                for r in inputs["physical"]["rows"]}
    roles = {(r["scene"], r["ann_id"]): r for r in inputs["roles"]["rows"]}
    units = defaultdict(list)
    exclusions = []
    for key in sorted(old):
        a, b = old[key], new[key]
        if "replay" not in a or "replay" not in b:
            exclusions.append({"scene": key[0], "ann_id": key[1],
                               "ordered": a.get("replay_exclusion"),
                               "score": b.get("replay_exclusion")})
            continue
        if (abs(a["replay"]["baseline_sample_loss"] -
                b["replay"]["baseline_sample_loss"]) > 1e-6
                or abs(a["replay"]["treated_sample_loss"] -
                       b["replay"]["treated_sample_loss"]) > 1e-6):
            raise ValueError("Baseline or treatment changed across controls")
        role = sorted({value for mention in roles[key]["mentions"]
                       for value in mention["roles"]})
        row = {
            "scene": key[0], "ann_id": key[1],
            "target_instances": b["target_instances"],
            "target_is_curtain": physical[key]["target_is_curtain"],
            "roles": role,
            "baseline_score_pair_abs_mean": b["baseline_score_pair_abs_mean"],
            "ordered_loss_contrast": (a["replay"]["treated_sample_loss"] -
                                      a["replay"]["placebo_sample_loss"]),
            "score_loss_contrast": (b["replay"]["treated_sample_loss"] -
                                    b["replay"]["placebo_sample_loss"]),
            "score_grad_delta_contrast": (
                b["sampler_parameter_backward"]["treated_delta_l1"] -
                b["sampler_parameter_backward"]["placebo_delta_l1"]),
        }
        units[(key[0], tuple(b["target_instances"]))].append(row)
    scene_targets = []
    for (scene, target), descriptions in sorted(units.items()):
        scene_targets.append({
            "scene": scene, "target_instances": target,
            "descriptions": len(descriptions),
            "score_loss_contrast": mean([r["score_loss_contrast"]
                                         for r in descriptions]),
            "score_grad_delta_contrast": mean([
                r["score_grad_delta_contrast"] for r in descriptions]),
        })
    scenes = []
    for scene in sorted({unit["scene"] for unit in scene_targets}):
        selected = [unit for unit in scene_targets if unit["scene"] == scene]
        scenes.append({
            "scene": scene, "scene_target_units": len(selected),
            "score_loss_contrast": mean([u["score_loss_contrast"]
                                         for u in selected]),
            "score_grad_delta_contrast": mean([
                u["score_grad_delta_contrast"] for u in selected]),
        })
    result = {
        "contract": "m95_full_train_score_control_grouped_v1",
        "admission": False,
        "inputs": {name: sha for name, (_, sha) in INPUTS.items()},
        "common_expressions": sum(map(len, units.values())),
        "score_replayed": score["summary"]["replayed"],
        "ordered_replayed": ordered["summary"]["replayed"],
        "excluded_from_common": exclusions,
        "scene_target_units": len(scene_targets),
        "scene_aggregates": scenes,
        "negative_score_loss_rows": sum(
            r["score_loss_contrast"] < 0 for rows in units.values() for r in rows),
        "positive_score_gradient_rows": sum(
            r["score_grad_delta_contrast"] > 0
            for rows in units.values() for r in rows),
        "mean_baseline_score_pair_abs": mean([
            r["baseline_score_pair_abs_mean"]
            for rows in units.values() for r in rows]),
        "limits": "Fixed TRAIN population; score matching does not match physical "
                  "geometry, role or hidden features. Existing sampler gradients "
                  "do not establish a new mechanism's trainability or efficacy.",
    }
    path = REPORTS / "m95_score_matched_grouped_20260928.json"
    if path.exists():
        raise ValueError("Refusing to replace evidence")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(json.dumps({
        "common": result["common_expressions"],
        "scene_target_units": result["scene_target_units"],
        "scenes": len(scenes),
        "negative_loss_rows": result["negative_score_loss_rows"],
        "positive_grad_rows": result["positive_score_gradient_rows"]}))


if __name__ == "__main__":
    main()
