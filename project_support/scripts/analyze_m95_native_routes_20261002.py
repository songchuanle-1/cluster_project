"""Validate repeat identities and summarize the two preregistered diagnostics."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numbers(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key != "repeat":
                yield from numbers(item)
    elif isinstance(value, list):
        for item in value:
            yield from numbers(item)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value):
            raise ValueError("Nonfinite diagnostic value")
        yield float(value)


def repeat_check(rows, key, strict=True):
    groups = [{key(row): row for row in rows if row["repeat"] == repeat}
              for repeat in (0, 1)]
    if any(sum(row["repeat"] == repeat for row in rows) != len(groups[repeat])
           for repeat in (0, 1)) or not groups[0] or groups[0].keys() != groups[1].keys():
        raise ValueError("Repeat identity/coverage mismatch")
    maximum = 0.0
    for identity, first in groups[0].items():
        second = groups[1][identity]
        if first.get("batch_input_sha256") != second.get("batch_input_sha256"):
            raise ValueError("Native input fingerprint drift")
        a, b = list(numbers(first)), list(numbers(second))
        if len(a) != len(b):
            raise ValueError("Repeat metric shape mismatch")
        error = max((abs(x - y) for x, y in zip(a, b)), default=0.0)
        maximum = max(maximum, error)
        if strict and error > 1e-6:
            raise ValueError("Repeat numeric drift exceeds frozen tolerance")
    return {"units_per_repeat": len(groups[0]), "max_absolute_metric_drift": maximum,
            "status": "PASS" if maximum <= 1e-6 else "FAIL",
            "frozen_tolerance": 1e-6}


def summarize_jacobian(source):
    if source["contract"] != "m95_native_task_jacobian_v1" or source["admission"]:
        raise ValueError("Diagnostic contract mismatch")
    repeat = repeat_check(source["rows"], lambda r: (r["batch"], r["scene"], r["ann_id"]),
                          strict=False)
    parameters_repeat = repeat_check(source["parameter_rows"], lambda r: r["batch"],
                                     strict=False)
    rows = [r for r in source["rows"] if r["repeat"] == 0 and r["frozen"]]
    if len(rows) != source.get("frozen_expressions", 31):
        raise ValueError("Frozen Jacobian cohort differs")
    pairs = {}
    for name in ("mask/referent", "mask/semantic", "referent/semantic"):
        native = [r["pairs"][name]["native"]["cosine"] for r in rows]
        rotated = [r["pairs"][name]["rotated"]["cosine"] for r in rows]
        valid = [(a, b) for a, b in zip(native, rotated) if a is not None and b is not None]
        pairs[name] = {
            "defined": len(valid),
            "native_mean_cosine": statistics.mean(a for a, _ in valid),
            "rotated_mean_cosine": statistics.mean(b for _, b in valid),
            "negative_native": sum(a < 0 for a, _ in valid),
        }
    parts = {
        name: {"nonzero": sum(r["descent"][name]["norms"][0] > 0 for r in rows),
               "adversely_directed": sum(r["descent"][name]["dot"] < 0 for r in rows)}
        for name in ("mask", "referent", "semantic", "quality")
    }
    parameter_rows = [r for r in source["parameter_rows"] if r["repeat"] == 0]
    second = {(r["batch"], r["scene"], r["ann_id"]): r
              for r in source["rows"] if r["repeat"] == 1}
    directional_agreement = {
        name: sum((r["descent"][name]["dot"] < 0) ==
                  (second[(r["batch"], r["scene"], r["ann_id"])]["descent"][name]["dot"] < 0)
                  for r in rows)
        for name in parts
    }
    scenes = {}
    for scene in sorted({r["scene"] for r in rows}):
        group = [r for r in rows if r["scene"] == scene]
        scenes[scene] = {
            "expressions": len(group),
            "mask_referent_mean_cosine": statistics.mean(
                r["pairs"]["mask/referent"]["native"]["cosine"] for r in group),
            "referent_semantic_mean_cosine": statistics.mean(
                r["pairs"]["referent/semantic"]["native"]["cosine"] for r in group),
            "referent_adverse": sum(r["descent"]["referent"]["dot"] < 0 for r in group),
            "mask_adverse": sum(r["descent"]["mask"]["dot"] < 0 for r in group),
        }
    parameter_pairs = {}
    for name in pairs:
        values = [r["pairs"][name]["cosine"] for r in parameter_rows
                  if r["pairs"][name]["cosine"] is not None]
        parameter_pairs[name] = {
            "defined_batches": len(values), "mean_cosine": statistics.mean(values),
            "negative_batches": sum(x < 0 for x in values),
        }
    return {
        "repeat": repeat, "parameters_repeat": parameters_repeat,
        "frozen_expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
        "query_pairs": pairs, "native_summed_update": parts,
        "final_ffn_parameter_pairs": parameter_pairs,
        "directional_repeat_agreement": directional_agreement,
        "scene_readouts": scenes,
        "max_native_gradient_sum_error": max(r["query_gradient_sum_error"] for r in rows),
        "interpretation": "Native referent and semantic objectives align, mask/referent are near orthogonal. No general adverse referent update; do not implement generic task-gradient surgery from this cohort. One adverse mask expression remains a diagnostic flag, not an efficacy veto.",
    }


def summarize_ownership(source):
    if source["contract"] != "m95_distinct_referent_ownership_v1" or source["admission"]:
        raise ValueError("Ownership contract mismatch")
    repeat = repeat_check(source["rows"], lambda r: (r["batch"], *r["ann_ids"]), strict=False)
    outcomes_repeat = repeat_check(source["outcomes"],
                                  lambda r: (r["batch"], r["scene"], r["ann_id"]), strict=False)
    rows = [r for r in source["rows"] if r["repeat"] == 0]
    second = {(r["batch"], *r["ann_ids"]): r
              for r in source["rows"] if r["repeat"] == 1}
    return {
        "repeat": repeat, "outcomes_repeat": outcomes_repeat,
        "distinct_target_pairs": len(rows), "scenes": len({r["scene"] for r in rows}),
        "pairs_with_failure": sum(r["either_failed"] for r in rows),
        "selected_target_overlap_pairs": sum(r["selected_overlap_on_target"] > 0 for r in rows),
        "native_matched_target_overlap_pairs": sum(r["matched_overlap_on_target"] > 0 for r in rows),
        "same_target_exclusions": sum(r["repeat"] == 0 for r in source["exclusions"]),
        "both_margin_direction_repeat_agreement": {
            arm: sum(all(
                (r["probe"][arm]["margin_velocity"][k] > 0) ==
                (second[(r["batch"], *r["ann_ids"])]["probe"][arm]["margin_velocity"][k] > 0)
                for k in range(2)) for r in rows)
            for arm in ("joint", "independent", "shifted_joint")
        },
        "gradient_mean_cosine_joint_vs_independent": statistics.mean(
            r["probe"]["joint_independent_gradient_cosine"] for r in rows),
        "arms": {
            arm: {
                "both_margin_directions_corrective": sum(
                    min(r["probe"][arm]["margin_velocity"]) > 0 for r in rows),
                "mean_corrective_cosine": statistics.mean(
                    r["probe"][arm]["corrective_cosine"] for r in rows),
            } for arm in ("joint", "independent", "shifted_joint")
        },
        "interpretation": "Physical correspondence matters, but categorical ownership supplies the same correction as existing independent BCE on every eligible pair. Do not admit the generic categorical realization as a new mechanism. No assertion that future joint structures cannot learn.",
    }


def main():
    parser = argparse.ArgumentParser()
    for key in ("jacobian", "ownership", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Fresh output required")
    report = {
        "contract": "m95_native_routes_repeat_summary_v1", "admission": False,
        "source_sha256": {"jacobian": digest(args.jacobian), "ownership": digest(args.ownership)},
        "jacobian": summarize_jacobian(json.loads(args.jacobian.read_text(encoding="utf-8"))),
        "ownership": summarize_ownership(json.loads(args.ownership.read_text(encoding="utf-8"))),
        "limitations": "Jacobian cohort size/scenes are explicitly reported; ownership cohort is 31 frozen expressions/2 scenes plus native companions. Prediction-blind selection within existing narrow cohorts; no population effect, trained benefit or new-candidate backward. Strict repeat FAIL is not relaxed. No optimizer, new model/config, admission, queue or training.",
    }
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
