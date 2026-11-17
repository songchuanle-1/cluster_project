"""D2 read-only diagnostic: does selection failure scale with same-category competition?

Reads only the frozen d1_instance_audit.json and d1_calibration.json rows.
No model load, no inference, no CUDA, no queue or trainer change.
"""
import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path("D:/project/cluster_project")
OUT = ROOT / "pipeline/reports/d2_competition_20260911-2207"
INSTANCE = ROOT / "pipeline/reports/d1_instance_20260911-0810/instance_audit.json"
CALIB = ROOT / "pipeline/reports/d1_calibration_20260911-1815/calibration.json"
BINS = OrderedDict([("0", (0, 0)), ("1-2", (1, 2)), ("3-5", (3, 5)),
                    ("6-10", (6, 10)), (">10", (11, 10 ** 9))])


def bin_of(n):
    if n is None:
        return "NA"
    for name, (lo, hi) in BINS.items():
        if lo <= n <= hi:
            return name
    raise ValueError(n)


def main():
    inst = json.loads(INSTANCE.read_text(encoding="utf-8"))
    calib = json.loads(CALIB.read_text(encoding="utf-8"))
    cal_rows = {(r["model"], r["identity"]["scene_id"], r["identity"]["object_id"],
                 r["identity"]["ann_id"]): r for r in calib["rows"]}

    out = {"source_instance_sha256": inst["source_sha256"],
           "source_calibration_sha256": calib["source_sha256"], "models": {}}
    for model in ("baseline", "m95"):
        rows = [r for r in inst["rows"] if r["model"] == model]
        buckets = {k: [] for k in list(BINS) + ["NA"]}
        for r in rows:
            buckets[bin_of(r["selected"]["same_semantic_other_instances"])].append(r)
        table = []
        for name, group in buckets.items():
            if not group:
                continue
            fail = [r for r in group if r["selected_iou"] <= 0.5]
            rec = [r for r in fail if r["oracle_iou"] > 0.5]
            wrong = [r for r in rec
                     if r["selected"].get("best_instance") != r["oracle"].get("best_instance")]
            table.append({
                "distractors": name, "banks": len(group),
                "selection_failures": len(fail),
                "selection_fail_rate": round(len(fail) / len(group), 4),
                "recoverable": len(rec),
                "recoverable_wrong_instance": len(wrong),
                "wrong_instance_fraction_of_recoverable": (
                    round(len(wrong) / len(rec), 4) if rec else None),
            })
        # Score calibration on recoverable vs success banks (from the frozen calibration rows).
        cal = [r for r in calib["rows"] if r["model"] == model]
        def margin_stats(stratum):
            g = [r for r in cal if r["stratum"] == stratum]
            margins = [r["score_of_selected"] - r["score_of_oracle"] for r in g]
            ranks = [r["oracle_score_rank"] for r in g]
            return {"banks": len(g),
                    "median_oracle_score_rank": sorted(ranks)[len(ranks) // 2],
                    "mean_oracle_score_rank": round(sum(ranks) / len(ranks), 2),
                    "median_selected_minus_oracle_score": round(
                        sorted(margins)[len(margins) // 2], 4)}
        out["models"][model] = {
            "distractor_table": table,
            "calibration": {s: margin_stats(s) for s in ("recoverable", "success")},
        }

    # Monotone-invariance note: any strictly increasing transform of a per-candidate
    # score preserves within-bank order, so it cannot move a candidate across the
    # selected/oracle boundary. This is a proof obligation, not a measurement.
    out["monotone_recalibration_note"] = (
        "Within a fixed candidate bank, argmax is invariant under any strictly "
        "increasing transform of the per-candidate score. Therefore per-bank score "
        "standardization, temperature rescaling, or min-max normalization cannot "
        "change the selected candidate; only a mechanism that changes the score "
        "field (new evidence or new supervision) can fix the measured error.")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "distractor_stratification.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    for model, m in out["models"].items():
        print("===", model)
        for row in m["distractor_table"]:
            print(" ", row)
        print("  calibration:", m["calibration"])
    print("wrote", OUT / "distractor_stratification.json")


if __name__ == "__main__":
    main()
