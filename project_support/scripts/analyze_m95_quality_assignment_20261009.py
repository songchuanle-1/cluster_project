"""Summarize the preregistered capture; keep repeat failures explicit."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(data):
    if data.get("contract") != "m95_quality_assignment_capture_v1":
        raise ValueError("Unexpected capture contract")
    records = data["records"]
    repeats = {}
    for repeat in (0, 1):
        selected = [r for r in records if r["repeat"] == repeat and r["frozen"]]
        by_id = {(r["scene"], r["ann_id"]): r for r in selected}
        if len(selected) != 31 or len(by_id) != 31:
            raise ValueError("Incomplete or duplicate frozen cohort")
        repeats[repeat] = by_id
    if repeats[0].keys() != repeats[1].keys():
        raise ValueError("Repeat expression IDs differ")
    fields = ("queries", "matched", "supervised", "censored", "qids",
              "selected_query", "selected_is_matched",
              "all_layer_assignments_identical", "score_gradient_nonzero_queries",
              "score_gradient_finite", "input_sha256")
    discrete_agreement = all(
        all(a[field] == repeats[1][key][field] for field in fields)
        for key, a in repeats[0].items())
    differences = []
    for key, a in repeats[0].items():
        b = repeats[1][key]
        if len(a["quality"]) != len(b["quality"]) or len(a["scores"]) != len(b["scores"]):
            raise ValueError("Repeat vector sizes differ")
        differences.extend(abs(x - y) for field in ("quality", "scores")
                           for x, y in zip(a[field], b[field]))
        differences.append(abs(a["selected_iou"] - b["selected_iou"]))
    drift = max(differences, default=0.0)
    frozen = list(repeats[0].values())
    companions = [r for r in records if r["repeat"] == 0 and not r["frozen"]]
    batches = [b for b in data["batches"] if b["repeat"] == 0]
    if not batches:
        raise ValueError("Missing native batches")
    layer_count = batches[0]["layer_count"]
    if layer_count < 2 or not all(
            b["layer_count"] == layer_count == len(b["assignments"]) == len(b["layers"])
            for b in data["batches"]):
        raise ValueError("Final/auxiliary loss call counts differ")

    def counts(rows):
        return {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "matched_query_targets": sum(r["matched"] for r in rows),
            "supervised_query_targets": sum(r["supervised"] for r in rows),
            "censored_query_targets": sum(r["censored"] for r in rows),
            "expressions_with_censoring": sum(r["censored"] > 0 for r in rows),
            "selected_is_matched": sum(r["selected_is_matched"] for r in rows),
            "selected_is_censored": sum(
                r["selected_is_matched"] and any(
                    q == r["selected_query"] and quality <= 0.5
                    for q, quality in zip(r["qids"], r["quality"]))
                for r in rows),
            "all_layers_identical": sum(r["all_layer_assignments_identical"] for r in rows),
            "finite_score_gradients": sum(r["score_gradient_finite"] for r in rows),
        }

    return {
        "contract": "m95_quality_assignment_analysis_v1", "admission": False,
        "frozen": counts(frozen), "companions": counts(companions),
        "batches_per_repeat": len(batches),
        "native_loss_calls_per_batch": layer_count,
        "native_layer_assignment_agreement": all(
            len(set(b["assignments"])) == 1 for b in data["batches"]),
        "rotated_control_differs": all(b["rotated_control_differs"] for b in data["batches"]),
        "repeat": {"tolerance": 1e-6, "max_absolute_drift": drift,
                   "discrete_agreement": discrete_agreement,
                   "status": "PASS" if discrete_agreement and drift <= 1e-6 else "FAIL"},
        "stage_totals": [
            {"stage_call": layer,
             "matched": sum(b["layers"][layer]["matched"] for b in batches),
             "censored": sum(b["layers"][layer]["censored"] for b in batches)}
            for layer in range(layer_count)],
        "elapsed_seconds": data["elapsed_seconds"],
        "peak_allocated_mib": data["peak_allocated_mib"],
        "training_started": False,
        "limitations": [
            "31-expression two-scene frozen TRAIN cohort, not all ScanRefer.",
            "Eval-mode TRAIN-loader capture, no optimizer and no candidate model.",
            "Coverage establishes a supervision fact, not trained benefit or admission.",
            "Depth equality rejects rematching only, not all decoder mechanisms.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = summarize(json.loads(args.capture.read_text(encoding="utf-8")))
    summary["capture"] = {"path": str(args.capture), "sha256": sha(args.capture)}
    summary["analyzer_sha256"] = sha(Path(__file__))
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(summary, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
