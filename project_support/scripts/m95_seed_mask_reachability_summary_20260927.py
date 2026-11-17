"""Bind selected native seed membership to the unchanged M95 capture."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "pipeline/reports"
SOURCE = REPORT / "m95_seed_mask_reachability_1999_20260927.json"
BASE = REPORT / "m95_seed_exact_1999_20260927.json"
PREREG = REPORT / "m95_seed_mask_reachability_prereg_20260927.md"
OUTPUT = REPORT / "m95_seed_mask_reachability_summary_20260927.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUTPUT.exists():
        raise ValueError("Summary exists")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    base = json.loads(BASE.read_text(encoding="utf-8"))
    rows = source["rows"]
    prior = {(r["scene"], r["ann_id"]): r for r in base["rows"]}
    keys = {(r["scene"], r["ann_id"]) for r in source["population_selected"]}
    if len(rows) != 128 or len(prior) != 128 or len(keys) != 32:
        raise ValueError("Native cohort incomplete")
    for row in rows:
        previous = prior.pop((row["scene"], row["ann_id"]))
        if (row["batch_input_sha256"] != previous["batch_input_sha256"]
                or row["selected_seed"] != previous["selected_seed"]
                or row["selected_seed_is_context"]
                != previous["selected_seed_is_context"]):
            raise ValueError("Same-input selection differs")
    if prior:
        raise ValueError("Native rows absent")
    exposed = [r for r in rows if r["selected_seed_is_context"]]
    controls = [r for r in rows if not r["selected_seed_is_context"]]
    cohort = [r for r in exposed if (r["scene"], r["ann_id"]) in keys]
    result = {
        "contract": "m95_seed_mask_reachability_summary_v1",
        "admission": False,
        "source_sha256": sha(SOURCE),
        "same_seed_base_sha256": sha(BASE),
        "prereg_sha256": sha(PREREG),
        "all_expressions": len(rows),
        "selected_context": len(exposed),
        "selected_context_seed_in_selected_mask": sum(
            r["selected_seed_in_selected_mask"] for r in exposed),
        "other_selected": len(controls),
        "other_seed_in_selected_mask": sum(
            r["selected_seed_in_selected_mask"] for r in controls),
        "preregistered_selected_context": len(cohort),
        "preregistered_context_seed_in_mask": sum(
            r["selected_seed_in_selected_mask"] for r in cohort),
        "selected_context_mask_seed_instance_iou_mean": (
            sum(r["selected_mask_seed_instance_iou"] for r in exposed)
            / len(exposed)),
        "selected_context_keys": [
            {"scene": r["scene"], "ann_id": r["ann_id"],
             "seed_instance": r["selected_seed_instance"],
             "mask_seed_instance_iou": r["selected_mask_seed_instance_iou"],
             "selected_target_iou": r["selected_mask_iou"]}
            for r in exposed
        ],
        "limits": (
            "Membership supports a possible seed-to-mask path on this fixed "
            "checkpoint, not a causal training effect. The proposed instance "
            "group mechanism and matched controls remain unimplemented; "
            "do not infer mIoU gain from this read-only screen."
        ),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "selected_context", "selected_context_seed_in_selected_mask",
        "other_selected", "other_seed_in_selected_mask",
        "preregistered_selected_context")}))


if __name__ == "__main__":
    main()
