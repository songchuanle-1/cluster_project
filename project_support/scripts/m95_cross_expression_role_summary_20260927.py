"""Validate the native cross-expression instance-role diagnostic."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "pipeline/reports"
SOURCE = REPORT / "m95_cross_expression_role_1999_20260927.json"
BASE = REPORT / "m95_seed_exact_1999_20260927.json"
OUTPUT = REPORT / "m95_cross_expression_role_summary_20260927.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(source, base):
    rows = source["rows"]
    previous = {(r["scene"], r["ann_id"]): r for r in base["rows"]}
    if (len(rows) != 128 or source["transform_seed"] != 1999
            or source["population_manifest_sha256"] != base["population_manifest_sha256"]
            or len(previous) != 128):
        raise ValueError("Native cohort identity differs")
    groups = defaultdict(lambda: defaultdict(set))
    per_row = []
    fractional = 0
    for row in rows:
        key = row["scene"], row["ann_id"]
        old = previous.pop(key)
        if (old["batch_input_sha256"] != row["batch_input_sha256"]
                or old["selected_seed"] != row["selected_seed"]
                or old["selected_seed_is_context"] != row["selected_seed_is_context"]
                or (old["selected_mask_iou"] > .5) != (row["selected_mask_iou"] > .5)):
            raise ValueError("Same-input selected endpoint differs")
        for seed, instance, value in row["unprotected_seed_roles"]:
            if value not in (0.0, 0.25):
                if not 0.0 < value < 0.25:
                    raise ValueError("Unexpected unprotected role")
                fractional += 1
                continue
            groups[(row["scene"], instance)][row["ann_id"]].add(value)
        per_row.append(row)
    if previous:
        raise ValueError("Missing native row")
    mixed = {
        key: entries for key, entries in groups.items()
        if any(.25 in vals for vals in entries.values())
        and any(0.0 in vals for vals in entries.values())
    }
    selected = [
        {"scene": row["scene"], "ann_id": row["ann_id"],
         "instance": row["selected_seed_instance"],
         "iou": row["selected_mask_iou"],
         "cross_expression_zero": any(
             0.0 in vals for ann, vals in
             mixed.get((row["scene"], row["selected_seed_instance"]), {}).items()
             if ann != row["ann_id"])}
        for row in per_row if row["selected_seed_is_context"]
    ]
    return {
        "contract": "m95_cross_expression_role_summary_v1",
        "admission": False,
        "native_expressions": len(rows),
        "scenes": len({r["scene"] for r in rows}),
        "physical_instances_with_unprotected_seeds": len(groups),
        "fractional_unprotected_seeds_excluded": fractional,
        "mixed_role_instances": len(mixed),
        "mixed_role_scenes": len({scene for scene, _ in mixed}),
        "selected_context": selected,
        "selected_context_with_cross_expression_zero": sum(
            r["cross_expression_zero"] for r in selected),
        "mixed_instance_keys": [
            {"scene": scene, "instance": instance,
             "context_ann_ids": sorted(ann for ann, vals in entries.items()
                                       if .25 in vals),
             "zero_ann_ids": sorted(ann for ann, vals in entries.items()
                                    if 0.0 in vals)}
            for (scene, instance), entries in sorted(mixed.items())
        ],
        "limits": (
            "Same physical instance and scene, but different expression and "
            "often target identity. Descriptive label contract, no causal "
            "same-forward control or model effect. Native 0.25 is a class-context "
            "cue, not a mistaken target label by itself."
        ),
    }


def main():
    if OUTPUT.exists():
        raise ValueError("Output exists")
    result = analyze(
        json.loads(SOURCE.read_text(encoding="utf-8")),
        json.loads(BASE.read_text(encoding="utf-8")))
    result["source_sha256"] = sha(SOURCE)
    result["same_seed_base_sha256"] = sha(BASE)
    result["prereg_sha256"] = sha(REPORT / "m95_cross_expression_role_prereg_20260927.md")
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "native_expressions", "scenes", "mixed_role_instances",
        "mixed_role_scenes", "selected_context_with_cross_expression_zero")}))


if __name__ == "__main__":
    main()
