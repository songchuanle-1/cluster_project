"""Compare exact-capture identity analysis with the frozen reference.

The match-cause capture is only causally interpretable if the fresh full scan
reproduces the previously frozen selector trajectories. This checker is
CPU-only and fail-closed.
"""
import json
import math
from pathlib import Path

from analyze_m95_manifest_identity_controls_20260922 import file_sha256


ROOT = Path(__file__).resolve().parent.parent
REFERENCE_ANALYSIS_NAME = "m95_identity_control_analysis_20260924-231333.json"
REFERENCE_ANALYSIS_SHA256 = (
    "c7b6e78c64e29144d3abfea5007e5ec0843142b3e7aa6294c600e8eb114d4abb"
)
REFERENCE_CAPTURE_SHA256 = (
    "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025"
)
EXPECTED_MANIFEST_SHA256 = (
    "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
)
EXPECTED_CHECKPOINT_SHA256 = (
    "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
)
CONTRACT = "m95_exact_capture_identity_reproducibility_v1"


def discover_reference_analysis(path=None):
    if path is not None:
        return Path(path)
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "pipeline" / "reports" / REFERENCE_ANALYSIS_NAME
        if candidate.is_file():
            return candidate
        if parent.name == "pipeline":
            candidate = parent / "reports" / REFERENCE_ANALYSIS_NAME
            if candidate.is_file():
                return candidate
    return here.parents[1] / "pipeline" / "reports" / REFERENCE_ANALYSIS_NAME


REFERENCE_ANALYSIS_PATH = discover_reference_analysis()


def _rows_by_index(document, label):
    rows = document.get("rows")
    if not isinstance(rows, list) or len(rows) != 256:
        raise ValueError("%s does not contain 256 analysis rows" % label)
    by_index = {}
    for row in rows:
        index = int(row.get("manifest_index", -1))
        if index in by_index:
            raise ValueError("%s contains duplicate manifest index" % label)
        by_index[index] = row
    if set(by_index) != set(range(256)):
        raise ValueError("%s manifest coverage differs" % label)
    return by_index


def _numeric_list(value, label):
    if not isinstance(value, list):
        raise ValueError("%s is not a list" % label)
    values = []
    for item in value:
        if item is None:
            values.append(None)
            continue
        number = float(item)
        if not math.isfinite(number):
            raise ValueError("%s contains a non-finite value" % label)
        values.append(number)
    return values


def _compare_list(
    reference,
    candidate,
    label,
    tolerance,
    mismatches,
    numeric=False,
):
    if len(reference) != len(candidate):
        mismatches.append(
            {"field": label, "reason": "length", "reference": len(reference),
             "candidate": len(candidate)}
        )
        return 0
    for position, (left, right) in enumerate(zip(reference, candidate)):
        if left is None or right is None:
            if left is not right:
                mismatches.append(
                    {"field": "%s[%d]" % (label, position), "reason": "null",
                     "reference": left, "candidate": right}
                )
            continue
        if numeric:
            if abs(float(left) - float(right)) > tolerance:
                mismatches.append(
                    {"field": "%s[%d]" % (label, position),
                     "reason": "tolerance", "reference": left,
                     "candidate": right}
                )
        elif left != right:
            mismatches.append(
                {"field": "%s[%d]" % (label, position), "reason": "value",
                 "reference": left, "candidate": right}
            )


def _max_abs_delta(reference, candidate, label, tolerance):
    left = _numeric_list(reference, "reference " + label)
    right = _numeric_list(candidate, "candidate " + label)
    if len(left) != len(right):
        raise ValueError("%s axis differs" % label)
    maximum = 0.0
    compared = 0
    for a, b in zip(left, right):
        if a is None or b is None:
            if a is not b:
                raise ValueError("%s null pattern differs" % label)
            continue
        maximum = max(maximum, abs(a - b))
        compared += 1
    return {"compared": compared, "max_abs_delta": maximum}


def _compare_stage_identity(reference, candidate, tolerance, mismatches):
    if reference is None or candidate is None:
        if reference is not candidate:
            mismatches.append(
                {"field": "stage_identity", "reason": "null",
                 "reference": reference, "candidate": candidate}
            )
        return 1
    if set(reference) != set(candidate):
        mismatches.append(
            {"field": "stage_identity", "reason": "stages",
             "reference": sorted(reference), "candidate": sorted(candidate)}
        )
        return
    count = 0
    for stage in sorted(reference):
        left = reference[stage]
        right = candidate[stage]
        if set(left) != set(right):
            count += 1
            mismatches.append(
                {"field": "stage_identity.%s" % stage, "reason": "fields",
                 "reference": sorted(left), "candidate": sorted(right)}
            )
            continue
        for field in sorted(left):
            a, b = left[field], right[field]
            if a is None or b is None:
                if a is not b:
                    count += 1
                    mismatches.append(
                        {"field": "stage_identity.%s.%s" % (stage, field),
                         "reason": "null", "reference": a, "candidate": b}
                    )
            elif abs(float(a) - float(b)) > tolerance:
                count += 1
                mismatches.append(
                    {"field": "stage_identity.%s.%s" % (stage, field),
                     "reason": "tolerance", "reference": a, "candidate": b}
                )
    return count


def _compare_pair(reference, candidate, mismatches):
    if reference is None or candidate is None:
        if reference is not candidate:
            mismatches.append(
                {"field": "score_matched_pair", "reason": "null",
                 "reference": reference, "candidate": candidate}
            )
        return
    for field in ("positive_index", "negative_index"):
        if reference.get(field) != candidate.get(field):
            mismatches.append(
                {"field": "score_matched_pair.%s" % field,
                 "reason": "value", "reference": reference.get(field),
                 "candidate": candidate.get(field)}
            )
    for field in ("score_difference",):
        left, right = reference.get(field), candidate.get(field)
        if left is None or right is None:
            if left is not right:
                mismatches.append(
                    {"field": "score_matched_pair.%s" % field,
                     "reason": "null", "reference": left, "candidate": right}
                )
        elif abs(float(left) - float(right)) > 1e-6:
            mismatches.append(
                {"field": "score_matched_pair.%s" % field,
                 "reason": "tolerance", "reference": left, "candidate": right}
            )


def compare_identity_analyses(
    reference,
    candidate,
    score_tolerance=1e-6,
    iou_tolerance=1e-6,
    feature_tolerance=1e-6,
):
    """Return a reproducibility receipt or raise on malformed inputs."""
    if reference.get("contract") != "m95_manifest_identity_control_analysis_v1":
        raise ValueError("Reference analysis contract differs")
    if candidate.get("contract") != "m95_manifest_identity_control_analysis_v1":
        raise ValueError("Candidate analysis contract differs")
    if (
        reference.get("source_capture", {}).get("sha256")
        != REFERENCE_CAPTURE_SHA256
    ):
        raise ValueError("Reference capture identity differs")
    if reference.get("manifest", {}).get("sha256") != EXPECTED_MANIFEST_SHA256:
        raise ValueError("Reference manifest identity differs")
    if candidate.get("manifest", {}).get("sha256") != EXPECTED_MANIFEST_SHA256:
        raise ValueError("Candidate manifest identity differs")
    if (
        candidate.get("source_capture", {}).get("checkpoint_sha256")
        != EXPECTED_CHECKPOINT_SHA256
    ):
        raise ValueError("Candidate checkpoint identity differs")

    reference_rows = _rows_by_index(reference, "reference")
    candidate_rows = _rows_by_index(candidate, "candidate")
    mismatches = []
    score_deltas = []
    iou_deltas = []
    feature_mismatches = 0
    selector_mismatches = 0
    paired_rows = 0

    exact_fields = (
        "scene_id",
        "ann_id",
        "stratum",
        "query_count",
        "deployed_query",
        "target_positive_query",
        "target_objectness_query",
        "class_matched_selector_query",
        "class_matched_non_target_query",
    )
    for index in range(256):
        left = reference_rows[index]
        right = candidate_rows[index]
        for field in exact_fields:
            if left.get(field) != right.get(field):
                mismatches.append(
                    {"manifest_index": index, "field": field,
                     "reason": "value", "reference": left.get(field),
                     "candidate": right.get(field)}
                )
                if field.endswith("query"):
                    selector_mismatches += 1
        _compare_list(
            left.get("native_positive"), right.get("native_positive"),
            "native_positive", score_tolerance, mismatches
        )
        _compare_list(
            left.get("dominant_instance"), right.get("dominant_instance"),
            "dominant_instance", score_tolerance, mismatches
        )
        _compare_list(
            left.get("fps_seed_inside_target"),
            right.get("fps_seed_inside_target"),
            "fps_seed_inside_target",
            score_tolerance,
            mismatches,
        )
        try:
            score_delta = _max_abs_delta(
                left.get("scores"), right.get("scores"),
                "scores", score_tolerance
            )
            score_deltas.append(score_delta)
            if score_delta["max_abs_delta"] > score_tolerance:
                mismatches.append(
                    {"manifest_index": index, "field": "scores",
                     "reason": "tolerance",
                     "maximum_abs_delta": score_delta["max_abs_delta"]}
                )
        except ValueError as error:
            mismatches.append(
                {"manifest_index": index, "field": "scores",
                 "reason": str(error)}
            )
        try:
            iou_delta = _max_abs_delta(
                left.get("ious"), right.get("ious"),
                "ious", iou_tolerance
            )
            iou_deltas.append(iou_delta)
            if iou_delta["max_abs_delta"] > iou_tolerance:
                mismatches.append(
                    {"manifest_index": index, "field": "ious",
                     "reason": "tolerance",
                     "maximum_abs_delta": iou_delta["max_abs_delta"]}
                )
        except ValueError as error:
            mismatches.append(
                {"manifest_index": index, "field": "ious",
                 "reason": str(error)}
            )
        feature_mismatches += _compare_stage_identity(
            left.get("stage_identity"),
            right.get("stage_identity"),
            feature_tolerance,
            mismatches,
        )
        _compare_pair(
            left.get("score_matched_pair"),
            right.get("score_matched_pair"),
            mismatches,
        )
        if left.get("score_matched_pair") is not None:
            paired_rows += 1
        for prefix in (
            "positive_minus_deployed_iou",
            "class_selector_minus_deployed_iou",
            "objectness_minus_deployed_iou",
            "class_non_target_minus_deployed_iou",
            "primary_pair_iou_uplift",
            "primary_pair_score_difference",
        ):
            a, b = left.get(prefix), right.get(prefix)
            if a is None or b is None:
                if a is not b:
                    feature_mismatches += 1
                    mismatches.append(
                        {"manifest_index": index, "field": prefix,
                         "reason": "null", "reference": a, "candidate": b}
                    )
            elif abs(float(a) - float(b)) > iou_tolerance:
                feature_mismatches += 1
                mismatches.append(
                    {"manifest_index": index, "field": prefix,
                     "reason": "tolerance", "reference": a, "candidate": b}
                )

    maximum_score_delta = max(
        (entry["max_abs_delta"] for entry in score_deltas), default=0.0
    )
    maximum_iou_delta = max(
        (entry["max_abs_delta"] for entry in iou_deltas), default=0.0
    )
    return {
        "schema_version": 1,
        "contract": CONTRACT,
        "status": "pass" if not mismatches else "fail",
        "reference_analysis_sha256": REFERENCE_ANALYSIS_SHA256,
        "reference_capture_sha256": REFERENCE_CAPTURE_SHA256,
        "candidate_capture_sha256": candidate.get("source_capture", {}).get(
            "sha256"
        ),
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
        "comparison": {
            "rows": 256,
            "paired_rows": paired_rows,
            "selector_mismatches": selector_mismatches,
            "identity_feature_mismatches": feature_mismatches,
            "maximum_score_delta": maximum_score_delta,
            "maximum_iou_delta": maximum_iou_delta,
            "mismatch_count": len(mismatches),
        },
        "mismatches": mismatches,
        "admission": False,
        "not_evidence_of": [
            "admission",
            "native backward",
            "resource gate",
            "deployable efficacy",
            "population effect",
            "novelty",
            "whole-mechanism benefit",
        ],
    }


def validate_reference(path=None):
    path = discover_reference_analysis(path)
    if file_sha256(path) != REFERENCE_ANALYSIS_SHA256:
        raise ValueError("Frozen reference analysis hash differs")
    return json.loads(path.read_text(encoding="utf-8"))
