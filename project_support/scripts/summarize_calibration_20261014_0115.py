"""Aggregate only this tick's specified native diagnostic results."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "3aabc8207fea49ffb20003340e9bdfb9"
REPORTS = ROOT / "pipeline/reports"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def cohort(result):
    expressions = [expression for row in result["rows"]
                   for expression in row["calibration_readout"]["expressions"]]
    sites = [site for expression in expressions for site in expression["sites"]]
    repelling = [s for s in sites if s["fractional"] and s["total_derivative"] > 0]
    kinds = {
        "main_secondary": lambda s: s["main"] and any(s[k] > 0 for k in ("modify", "pron", "rel")),
        "relation_other": lambda s: s["rel"] > 0 and s["other"] > 0,
        "fractional_secondary": lambda s: s["fractional"]}
    roles = {}
    for name, predicate in kinds.items():
        selected = [s for s in sites if predicate(s)]
        roles[name] = {"query_token_sites": len(selected),
                       "direct_repelling_sites": sum(s["total_derivative"] > 0 for s in selected)}
    alignment = {}
    for name in (*kinds, "fractional_repelling", "fractional_attracting"):
        exposed = [e for e in expressions if name in e["role_task_alignment"]]
        direction = {
            objective: dict(Counter(
                "opposing" if e["role_task_alignment"][name][objective]["dot"] < 0 else
                "aligned" if e["role_task_alignment"][name][objective]["dot"] > 0 else "zero"
                for e in exposed))
            for objective in ("mask", "indicator", "mask_plus_indicator")}
        alignment[name] = {
            "expressions": len(exposed), "scenes": len({
                row["selection"]["scene"] for row in result["rows"]
                if any(name in e["role_task_alignment"] for e in row["calibration_readout"]["expressions"])}),
            "selected_support_failures": sum(e["selected_support_iou"] < .5 for e in exposed),
            "directions": direction}
    return {
        "groups": len(result["rows"]), "expressions": len(expressions),
        "scenes": len({row["selection"]["scene"] for row in result["rows"]}),
        "union_sites": len(sites), "roles": roles,
        "analytic_autograd_max_delta": max(
            row["calibration_readout"]["analytic_autograd_max_delta"] for row in result["rows"]),
        "fractional_repelling_sites": len(repelling),
        "repelling_above_query_token_threshold": sum(
            s["query_to_token_probability"] > s["calibration_threshold"] for s in repelling),
        "repelling_query_token_positive": sum(s["query_to_token_derivative"] > 0 for s in repelling),
        "repelling_token_query_negative": sum(s["token_to_query_derivative"] < 0 for s in repelling),
        "selected_support_failures": sum(e["selected_support_iou"] < .5 for e in expressions),
        "recoverable_support_failures": sum(
            e["selected_support_iou"] < .5 and e["best_support_iou"] >= .5 for e in expressions),
        "role_task_alignment": alignment,
        "missing_disjoint_controls": sum(len(row["missing_disjoint_controls"]) for row in result["rows"]),
        "peak_allocated_mib": result["allocator_peak_allocated_mib"],
        "peak_reserved_mib": result["allocator_peak_reserved_mib"],
        "scope": "Original TRAIN augmented support IoU/local derivatives, not VAL mIoU, causal effects or training outcomes."}


def heads(result):
    names = result["rows"][0]["calibration_readout"]["fixed_head"]["conditions"]
    summary = {}
    for name in names:
        values = [row["calibration_readout"]["fixed_head"]["conditions"][name]
                  for row in result["rows"]]
        active = [value for value in values if value["effects"] is not None]
        conditions = {}
        for objective in ("mask", "indicator", "mask_plus_indicator"):
            effects = [value["effects"][objective] for value in active]
            conditions[objective] = {
                "decreased_groups": sum(e["descent_loss_delta"] < 0 for e in effects),
                "increased_groups": sum(e["descent_loss_delta"] > 0 for e in effects),
                "zero_groups": sum(e["descent_loss_delta"] == 0 for e in effects),
                "maximum_absolute_loss_delta": max(
                    (abs(e["descent_loss_delta"]) for e in effects), default=None),
                "maximum_central_derivative_error": max(
                    (e["central_absolute_error"] for e in effects), default=None)}
        expression_counts = Counter()
        for row in result["rows"]:
            capture = row["calibration_readout"]
            value = capture["fixed_head"]["conditions"][name]
            if value["effects"] is None:
                continue
            for original, base, descent in zip(
                    capture["expressions"], capture["fixed_head"]["baseline"]["expressions"],
                    value["descent_expression_readouts"]):
                if name in ("main_secondary", "relation_other", "fractional_secondary",
                            "fractional_repelling", "fractional_attracting"):
                    if name not in original["role_task_alignment"]:
                        continue
                expression_counts["readouts"] += 1
                expression_counts["selected_query_changes"] += base["selected"] != descent["selected"]
                expression_counts["support_iou_changes"] += base["selected_support_iou"] != descent["selected_support_iou"]
                delta = descent["indicator_matched_unmatched_margin"] - base["indicator_matched_unmatched_margin"]
                expression_counts["margin_decreased" if delta < 0 else
                                  "margin_increased" if delta > 0 else "margin_unchanged"] += 1
        summary[name] = {"active_groups": len(active), "task_losses": conditions,
                         "expression_readouts": dict(expression_counts)}
    return {
        "groups": len(result["rows"]), "epsilon": .001,
        "identity_max_loss_delta": max(
            row["calibration_readout"]["fixed_head"]["head_identity_max_loss_delta"]
            for row in result["rows"]),
        "all_same_capture_head_repeats_exact": all(
            row["calibration_readout"]["fixed_head"]["same_capture_head_repeat_exact"]
            for row in result["rows"]), "conditions": summary,
        "scope": "Fixed heads only; float32 tiny effects are not material harm, full-network intervention, strict derivative certification or efficacy."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", action="store_true")
    args = parser.parse_args()
    prefixes = ("native_role_calibration_v2", "native_role_head",
                "native_calibration_supplement", "native_calibration_extension")
    paths = {prefix: REPORTS / (prefix + "_" + TOKEN + ".json") for prefix in prefixes}
    loaded = {prefix: read(path) for prefix, path in paths.items() if path.is_file()}
    primary = loaded["native_role_calibration_v2"]
    old = read(REPORTS / "native_role_direction_v2_f38daa9ab2914c97a74bd716613388f8.json")
    old_inputs = {r["selection"]["group"]: r["input_sha256"] for r in old["rows"]}
    assert all(r["input_sha256"] == old_inputs[r["selection"]["group"]] for r in primary["rows"])
    for prefix in ("native_role_head",):
        if prefix in loaded:
            assert all(r["input_sha256"] == old_inputs[r["selection"]["group"]]
                       for r in loaded[prefix]["rows"])
    summary = {
        "tick_token": TOKEN, "summarized_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_at": "2026-10-13T17:15:10.525220+00:00",
        "deadline_at": "2026-10-13T18:15:10.525220+00:00",
        "successful_gpu_runs": len(loaded), "gpu_adapter_failed_attempts": 1,
        "completed_group_readouts": sum(len(r["rows"]) for r in loaded.values()),
        "primary_input_fingerprints_match_frozen_prior": True,
        "cohorts": {prefix: cohort(result) for prefix, result in loaded.items()},
        "optimizer_steps": 0, "new_trainable_tensors": 0, "new_model_variants": 0,
        "training_admissions": 0, "training_launches": 0,
        "historical_full_forward_strict1e6_failures_retained": True,
        "evidence": [ref(paths[prefix]) for prefix in loaded],
        "scientific_status": "validation; original mechanics measured, independent structural intervention and training admission not established",
        "scope": "Partial diagnosis, not material task harm, official mIoU, uniform exclusive resource measurement, trained benefit or gate relaxation."}
    if "native_role_head" in loaded:
        summary["fixed_head"] = heads(loaded["native_role_head"])
    if args.output:
        assert len(loaded) == 4, "Do not finalize a summary with missing preregistered results"
        owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
        assert owner["token"] == TOKEN
        with (REPORTS / "native_calibration_summary_20261014_0115.json").open("x") as stream:
            json.dump(summary, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(json.dumps(summary, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
