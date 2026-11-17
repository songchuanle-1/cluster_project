"""Bounded, read-only decomposition of the failed M95 reproducibility gate."""
import argparse
import hashlib
import json
from pathlib import Path


REFERENCE_SHA256 = "c7b6e78c64e29144d3abfea5007e5ec0843142b3e7aa6294c600e8eb114d4abb"
EXPECTED_CAPTURE_SHA256 = "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"
EXPECTED_MANIFEST_SHA256 = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
EXPECTED_CHECKPOINT_SHA256 = "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rows_by_index(document):
    if document.get("contract") != "m95_manifest_identity_control_analysis_v1":
        raise ValueError("Identity analysis contract differs")
    if document.get("manifest", {}).get("sha256") != EXPECTED_MANIFEST_SHA256:
        raise ValueError("Manifest differs")
    rows = document.get("rows", [])
    by_index = {row["manifest_index"]: row for row in rows}
    if len(rows) != 256 or set(by_index) != set(range(256)):
        raise ValueError("Manifest row coverage differs")
    return by_index


def audit(reference, candidate):
    left = rows_by_index(reference)
    right = rows_by_index(candidate)
    if reference.get("source_capture", {}).get("sha256") != (
        "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025"
    ):
        raise ValueError("Reference capture differs")
    source = candidate.get("source_capture", {})
    if (source.get("sha256") != EXPECTED_CAPTURE_SHA256 or
            source.get("checkpoint_sha256") != EXPECTED_CHECKPOINT_SHA256):
        raise ValueError("Candidate capture or checkpoint differs")

    iou_drift = []
    score_drift_rows = []
    selector_changes = []
    threshold_flips = []
    selected_iou_changes = []
    pair_changes = []
    pair_score_drift = []
    for index in range(256):
        a, b = left[index], right[index]
        if a["scene_id"] != b["scene_id"] or a["ann_id"] != b["ann_id"]:
            raise ValueError("Expression binding differs")
        if len(a["ious"]) != 128 or len(b["ious"]) != 128 or (
            len(a["scores"]) != 128 or len(b["scores"]) != 128
        ):
            raise ValueError("Query axis differs")
        if a["deployed_query"] != b["deployed_query"]:
            selector_changes.append(index)
        selected = a["deployed_query"]
        if abs(a["ious"][selected] - b["ious"][selected]) > 1e-6:
            selected_iou_changes.append(index)
        pair_a, pair_b = a.get("score_matched_pair"), b.get("score_matched_pair")
        if (pair_a is None) != (pair_b is None):
            pair_changes.append(index)
        elif pair_a is not None:
            fields = ("positive_index", "negative_index", "tie_break_sha256")
            if any(pair_a.get(field) != pair_b.get(field) for field in fields):
                pair_changes.append(index)
            if abs(pair_a["score_difference"] - pair_b["score_difference"]) > 1e-6:
                pair_score_drift.append(index)
        maximum_score_delta = max(
            abs(x - y) for x, y in zip(a["scores"], b["scores"])
        )
        if maximum_score_delta > 1e-6:
            score_drift_rows.append({
                "manifest_index": index,
                "maximum_abs_delta": maximum_score_delta,
            })
        for query, (x, y) in enumerate(zip(a["ious"], b["ious"])):
            if abs(x - y) > 1e-6:
                iou_drift.append({
                    "manifest_index": index,
                    "scene_id": a["scene_id"],
                    "ann_id": a["ann_id"],
                    "query": query,
                    "reference_iou": x,
                    "candidate_iou": y,
                })
            if (x > 0.5) != (y > 0.5):
                threshold_flips.append([index, query])
    return {
        "contract": "m95_repro_drift_audit_v1",
        "strict_reproducibility_status": "fail",
        "rows": 256,
        "query_axis": 128,
        "score_drift_rows_over_1e-6": len(score_drift_rows),
        "score_drift_rows_over_1e-5": [
            row for row in score_drift_rows if row["maximum_abs_delta"] > 1e-5
        ],
        "maximum_score_delta": max(
            (row["maximum_abs_delta"] for row in score_drift_rows), default=0.0
        ),
        "iou_drift_queries": iou_drift,
        "selector_changes": selector_changes,
        "selected_iou_changes": selected_iou_changes,
        "iou_threshold_flips": threshold_flips,
        "score_matched_pair_changes": pair_changes,
        "score_matched_pair_score_drift_over_1e-6": pair_score_drift,
        "admission": False,
        "scope": "Read-only fixed-capture measurement audit; not a relaxed gate or model efficacy test.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if sha256(args.reference) != REFERENCE_SHA256:
        raise ValueError("Reference analysis hash differs")
    result = audit(load(args.reference), load(args.candidate))
    result["reference_sha256"] = REFERENCE_SHA256
    result["candidate_sha256"] = sha256(args.candidate)
    output = Path(args.output)
    if output.exists():
        raise ValueError("Output already exists")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps({key: value for key, value in result.items() if key not in (
        "iou_drift_queries", "score_drift_rows_over_1e-5"
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
