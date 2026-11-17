"""Bind frozen full-TRAIN outcomes to the score-matched native loss diagnosis."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "pipeline/reports"
SOURCES = {
    "outcome": ("m95_full_train_outcome_20260928-1202.json",
                "360950f4e27be4f0449965ee43866e512d071170277bfc769cc8a4ef0a3ad51e"),
    "score": ("m95_score_matched_20260928-1153.json",
              "e1fb561a18e4375cd1c5146e4587e78b381eb3ceaa4b3720a0536d90dfc72de2"),
}


def main():
    data = {}
    for name, (file, expected) in SOURCES.items():
        path = REPORTS / file
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"{name} hash differs")
        data[name] = json.loads(path.read_text(encoding="utf-8"))
    outcome = {(r["scene"], r["ann_id"]): r for r in data["outcome"]["rows"]}
    replay = {(r["scene"], r["ann_id"]): r for r in data["score"]["rows"]}
    if len(outcome) != 102 or len(replay) != 102 or outcome.keys() != replay.keys():
        raise ValueError("Frozen identities differ")
    rows = []
    units = defaultdict(list)
    for key in sorted(outcome):
        o, s = outcome[key], replay[key]
        failed = o["selected_mask_iou"] < 0.5
        row = {
            "scene": key[0], "ann_id": key[1],
            "target_instances": o["target_instances"],
            "failed": failed, "selected_mask_iou": o["selected_mask_iou"],
            "seed_majority_matches_target": o["seed_majority_matches_target"],
            "replayed": "replay" in s,
            "replay_exclusion": s.get("replay_exclusion"),
        }
        if row["replayed"]:
            row["loss_contrast"] = (s["replay"]["treated_sample_loss"] -
                                    s["replay"]["placebo_sample_loss"])
            row["gradient_contrast"] = (
                s["sampler_parameter_backward"]["treated_delta_l1"] -
                s["sampler_parameter_backward"]["placebo_delta_l1"])
        units[(key[0], tuple(o["target_instances"]))].append(row)
        rows.append(row)
    failure = [r for r in rows if r["failed"]]
    result = {
        "contract": "m95_full_train_outcome_loss_link_v1",
        "admission": False,
        "inputs": {key: value[1] for key, value in SOURCES.items()},
        "cohort": len(rows),
        "scenes": len({r["scene"] for r in rows}),
        "scene_target_units": len(units),
        "failures": len(failure),
        "failure_scenes": len({r["scene"] for r in failure}),
        "replayed": sum(r["replayed"] for r in rows),
        "replayed_failures": sum(r["replayed"] for r in failure),
        "replayed_failure_scenes": len({
            r["scene"] for r in failure if r["replayed"]}),
        "replayed_failure_loss_lower": sum(
            r["replayed"] and r["loss_contrast"] < 0 for r in failure),
        "unreplayed_failure_ids": [
            (r["scene"], r["ann_id"]) for r in failure if not r["replayed"]],
        "failure_units": [
            {"scene": scene, "target_instances": target,
             "expressions": len(group),
             "failed": sum(r["failed"] for r in group)}
            for (scene, target), group in sorted(units.items())
            if any(r["failed"] for r in group)],
        "rows": rows,
        "limits": "Frozen TRAIN outcomes are descriptive. Failure exposure is "
                  "concentrated in few scenes and does not demonstrate that "
                  "support repair changes inference or trained performance.",
    }
    path = REPORTS / "m95_full_train_outcome_link_20260928.json"
    if path.exists():
        raise ValueError("Refusing overwrite")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "cohort", "scenes", "scene_target_units", "failures",
        "failure_scenes", "replayed_failures", "replayed_failure_scenes",
        "replayed_failure_loss_lower")}))


if __name__ == "__main__":
    main()
