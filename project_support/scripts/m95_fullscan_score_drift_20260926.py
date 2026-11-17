"""Measure query-level score and mask drift in frozen M95 analyses."""
import argparse
import json
import math
from pathlib import Path

from m95_exact_capture_reproducibility_20260925 import (
    REFERENCE_ANALYSIS_SHA256,
)
from analyze_m95_manifest_identity_controls_20260922 import file_sha256


CURRENT_SHA256 = "f8456b4e5c2099af4162c00d2e81445e902290e7b3d4948201032a37eab8ea2a"
CENSUS_SHA256 = "7ba1234f57ff9345bb808d9191096cd508950f86b806218e3616b266d5ad5425"


def load(path, expected):
    if file_sha256(path) != expected:
        raise ValueError("Input hash differs")
    return json.loads(Path(path).read_text(encoding="utf-8"))


def summarize(reference, candidate, census):
    fps_rows = set(census["indices"]["entry_fps_differ"])
    assignment_rows = set(census["indices"]["assignment_differ"][0])
    if len(reference["rows"]) != 256 or len(candidate["rows"]) != 256:
        raise ValueError("Analysis rows differ")
    old = {int(row["manifest_index"]): row for row in reference["rows"]}
    new = {int(row["manifest_index"]): row for row in candidate["rows"]}
    if set(old) != set(new) or set(old) != set(range(256)):
        raise ValueError("Manifest coverage differs")
    groups = {"fps_changed": [], "fps_unchanged": []}
    for index in range(256):
        a, b = old[index], new[index]
        if len(a["scores"]) != len(b["scores"]) or len(a["ious"]) != len(b["ious"]):
            raise ValueError("Query axis differs")
        score_deltas = [abs(float(x) - float(y))
                        for x, y in zip(a["scores"], b["scores"])]
        iou_deltas = [abs(float(x) - float(y))
                      for x, y in zip(a["ious"], b["ious"])]
        if not all(map(math.isfinite, score_deltas + iou_deltas)):
            raise ValueError("Nonfinite query delta")
        row = {
            "manifest_index": index,
            "fps_changed": index in fps_rows,
            "assignment_changed": index in assignment_rows,
            "scores_above_1e-6": sum(x > 1e-6 for x in score_deltas),
            "max_score_delta": max(score_deltas),
            "ious_above_1e-6": sum(x > 1e-6 for x in iou_deltas),
            "max_iou_delta": max(iou_deltas),
            "selected_query_changed": a["deployed_query"] != b["deployed_query"],
            "selected_iou_changed": a["deployed_iou"] != b["deployed_iou"],
        }
        groups["fps_changed" if index in fps_rows else "fps_unchanged"].append(row)
    return {
        "contract": "m95_fullscan_score_drift_v1",
        "reference_analysis_sha256": REFERENCE_ANALYSIS_SHA256,
        "candidate_analysis_sha256": CURRENT_SHA256,
        "census_sha256": CENSUS_SHA256,
        "groups": {
            name: {
                "rows": len(rows),
                "score_drift_rows": sum(row["scores_above_1e-6"] > 0 for row in rows),
                "iou_drift_rows": sum(row["ious_above_1e-6"] > 0 for row in rows),
                "max_score_delta": max(row["max_score_delta"] for row in rows),
                "max_iou_delta": max(row["max_iou_delta"] for row in rows),
                "selected_query_changes": sum(row["selected_query_changed"] for row in rows),
                "selected_iou_changes": sum(row["selected_iou_changed"] for row in rows),
            } for name, rows in groups.items()
        },
        "fps_changed_rows": groups["fps_changed"],
        "all_iou_drift_rows": [row for rows in groups.values()
                               for row in rows if row["ious_above_1e-6"]],
        "strict_reproducibility_status": "fail",
        "admission": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("candidate")
    parser.add_argument("census")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise ValueError("Output already exists")
    result = summarize(
        load(args.reference, REFERENCE_ANALYSIS_SHA256),
        load(args.candidate, CURRENT_SHA256),
        load(args.census, CENSUS_SHA256),
    )
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(json.dumps(result["groups"]))


if __name__ == "__main__":
    main()
