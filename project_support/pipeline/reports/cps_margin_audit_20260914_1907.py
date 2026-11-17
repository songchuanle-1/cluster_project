"""Audit saved CPS pair margins; no model imports, training, or bank recapture."""
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


def loss_and_mass(delta):
    loss = max(-delta, 0.0) + math.log1p(math.exp(-abs(delta)))
    e = math.exp(-abs(delta))
    mass = e / (1.0 + e) if delta >= 0 else 1.0 / (1.0 + e)
    return loss, mass


def summarize(rows):
    scenes = defaultdict(list)
    for row in rows:
        scenes[row["scene_id"]].append(row)
    strata = {}
    for hard in (False, True):
        for positive in (False, True):
            selected = [r for r in rows if r["hard_failure"] == hard
                        and r["positive_delta"] == positive]
            strata[f"hard_failure={hard},positive_delta={positive}"] = {
                "pairs": len(selected),
                "scenes": len({r["scene_id"] for r in selected}),
                "loss_sum": math.fsum(r["loss"] for r in selected),
                "abs_dloss_ddelta_sum": math.fsum(r["mass"] for r in selected),
            }
    # Cluster resampling keeps correlated expression pairs together.
    counts = [(sum(r["hard_failure"] and r["positive_delta"] for r in group),
               sum(r["hard_failure"] for r in group))
              for _, group in sorted(scenes.items())]
    rng = random.Random(1999)
    values = []
    for _ in range(10000):
        sampled = rng.choices(counts, k=len(counts))
        denominator = sum(x[1] for x in sampled)
        if denominator:
            values.append(sum(x[0] for x in sampled) / denominator)
    values.sort()

    def quantile(p):
        position = (len(values) - 1) * p
        lo = int(position)
        hi = min(lo + 1, len(values) - 1)
        return values[lo] + (values[hi] - values[lo]) * (position - lo)

    failures = [r for r in rows if r["hard_failure"]]
    mass = math.fsum(r["mass"] for r in rows)
    return {
        "pairs": len(rows), "scenes": len(scenes), "cross_tab": strata,
        "both_row_correct_pairs": sum(r["both_row_correct"] for r in rows),
        "hard_failure_pairs": len(failures),
        "threshold_equality_pairs": sum(
            r["selected_iou_a"] == .5 or r["selected_iou_b"] == .5 for r in rows),
        "positive_delta_among_hard_failure": (
            sum(r["positive_delta"] for r in failures) / len(failures)
            if failures else None),
        "positive_delta_among_hard_failure_scene_bootstrap95": (
            [quantile(.025), quantile(.975)] if values else None),
        "bootstrap_valid_replicates": len(values),
        "loss_sum": math.fsum(r["loss"] for r in rows),
        "abs_dloss_ddelta_sum": mass,
        "hard_failure_derivative_mass_fraction": (
            math.fsum(r["mass"] for r in failures) / mass if mass else None),
    }


def self_test():
    assert loss_and_mass(0) == (math.log(2), .5)
    assert loss_and_mass(1000) == (0., 0.)
    assert loss_and_mass(-1000) == (1000., 1.)
    for d in (-12., -1., 0., 1., 12.):
        loss, mass = loss_and_mass(d)
        eps = 1e-5
        derivative = (loss_and_mass(d + eps)[0] -
                      loss_and_mass(d - eps)[0]) / (2 * eps)
        assert math.isclose(derivative, -mass, abs_tol=1e-9)
        assert math.isclose(mass + loss_and_mass(-d)[1], 1.)
    empty = summarize([])
    assert empty["pairs"] == 0
    assert empty["positive_delta_among_hard_failure_scene_bootstrap95"] is None


def main():
    self_test()
    root = Path(__file__).resolve().parent
    source = root / "cps_applicability_20260914.json"
    raw = source.read_bytes()
    data = json.loads(raw)
    rows = data["rows"]
    counts = Counter(r["status"] for r in rows)
    assert len(rows) == data["summary"]["pairs"] == 426
    assert counts == data["summary"]["status_counts"]
    assert len({r["scene_id"] for r in rows}) == 71
    eligible = []
    seen = set()
    for row in rows:
        if row["status"] != "eligible":
            continue
        a, b = row["a"], row["b"]
        assert a["scene_id"] == b["scene_id"] == row["scene_id"]
        assert a["object_id"] != b["object_id"]
        identity = (row["scene_id"], tuple(sorted(
            (str(r["object_id"]), str(r["ann_id"])) for r in (a, b))))
        assert identity not in seen
        seen.add(identity)
        cells = row["cells"]
        delta = cells[0][0] + cells[1][1] - cells[0][1] - cells[1][0]
        assert all(math.isfinite(x) for cell in cells for x in cell)
        assert math.isclose(delta, row["delta"], abs_tol=1e-8)
        assert math.isclose(cells[0][0] - cells[0][1],
                            row["row_a_margin"], abs_tol=1e-8)
        assert math.isclose(cells[1][1] - cells[1][0],
                            row["row_b_margin"], abs_tol=1e-8)
        assert all(0 <= row[key] <= 1 for key in ("selected_iou_a", "selected_iou_b"))
        loss, mass = loss_and_mass(delta)
        eligible.append({
            **row,
            "hard_failure": min(row["selected_iou_a"], row["selected_iou_b"]) <= .5,
            "positive_delta": delta > 0,
            "both_row_correct": row["row_a_margin"] > 0 and row["row_b_margin"] > 0,
            "loss": loss, "mass": mass,
        })
    summary = {"all": summarize(eligible),
               "same_category": summarize([r for r in eligible if r["same_category"]])}
    for key in summary:
        old = data["summary"][key]
        new = summary[key]
        assert new["pairs"] == old["pairs"]
        assert new["scenes"] == old["scenes"]
        assert new["hard_failure_pairs"] == old["at_least_one_hard_failure"]
        assert new["pairs"] - new["both_row_correct_pairs"] == old["not_both_row_correct"]
    result = {
        "source": source.name,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "hard_success_convention": "IoU > 0.5 for both expressions; matches source audit",
        "bootstrap": {"unit": "scene", "replicates": 10000, "seed": 1999},
        "limits": ["Failure-mined frozen M95 VAL, not population prevalence",
                   "Unweighted dL/dDelta, not full-loss parameter gradients",
                   "Not native TRAIN applicability or M195 efficacy evidence"],
        "self_tests": "passed", "input_status_counts": dict(counts),
        "summary": summary, "eligible_pair_records": eligible,
    }
    output = root / "cps_margin_audit_20260914-1907.json"
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                      encoding="utf-8")
    print(json.dumps({"output": str(output), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
