"""Partition exact M95 match-cause evidence after the native capture finishes.

This CPU-only diagnostic separates target-positive queries into the native
nearest-GT and instance-member causes. It evaluates oracle top-score choices
inside those sets and records paired differences against the deployed query.
It does not train, mutate the queue, or establish an admissible mechanism.
"""
import argparse
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path

from m95_match_cause_contract_20260923 import check_row


EXPECTED_MANIFEST_SHA256 = (
    "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
)
EXPECTED_CHECKPOINT_SHA256 = (
    "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
)
EXPECTED_PRODUCER_SHA256 = (
    "206c594d8c5219c6e249d89f7cb91815467bd443a030bc8bbd76d457de0b485a"
)
EXPECTED_ROWS = 256
EXPECTED_CAPTURE_MODE = "full_train_scan"
BOOTSTRAP_DRAWS = 10000
BOOTSTRAP_SEED = 1999
ANALYSIS_CONTRACT = "m95_exact_match_cause_partition_v1"
SELECTORS = (
    "deployed",
    "all_native_positive",
    "target_positive",
    "target_nearest",
    "target_member",
)
PAIRED_COMPARISONS = (
    "target_positive_minus_deployed",
    "all_native_positive_minus_deployed",
    "target_nearest_minus_deployed",
    "target_member_minus_deployed",
    "target_positive_minus_all_native_positive",
)


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_capture(capture):
    if capture.get("capture_mode") != EXPECTED_CAPTURE_MODE:
        raise ValueError("Capture is not the exact full-train scan")
    if capture.get("producer_sha256") != EXPECTED_PRODUCER_SHA256:
        raise ValueError("Capture producer differs from the frozen contract")
    if capture.get("manifest", {}).get("sha256") != EXPECTED_MANIFEST_SHA256:
        raise ValueError("Capture manifest differs from the frozen contract")
    if capture.get("checkpoint_sha256") != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError("Capture checkpoint differs from M95")
    for key in (
        "native_capture_completed",
        "native_match_cause_completed",
        "identity_query_completed",
    ):
        if capture.get(key) is not True:
            raise ValueError("Capture completion flag differs: %s" % key)
    if int(capture.get("selected_expressions", -1)) != EXPECTED_ROWS:
        raise ValueError("Capture selected-expression count differs")
    rows = capture.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_ROWS:
        raise ValueError("Capture does not contain 256 rows")
    by_index = {}
    for row in rows:
        index = int(row.get("manifest_index", -1))
        if index in by_index:
            raise ValueError("Duplicate capture manifest index")
        by_index[index] = row
    if set(by_index) != set(range(EXPECTED_ROWS)):
        raise ValueError("Capture manifest coverage differs")
    return by_index


def target_cause_sets(cause, target_object_id):
    object_ids = [int(value) for value in cause["object_ids"]]
    target = str(target_object_id)
    matches = [index for index, value in enumerate(object_ids) if str(value) == target]
    if len(matches) != 1:
        raise ValueError("Native target object binding differs")
    target_index = matches[0]
    nearest = {int(query) for query in cause["nearest_query_per_gt"]}
    members = {
        int(query)
        for group in cause["member_queries_per_gt"]
        for query in group
    }
    query_count = len(cause["sampled_pos"])
    target_nearest = {
        query
        for query, gt in enumerate(cause["nearest_query_per_gt"])
        if int(gt) == target_index
    }
    target_member = {
        query
        for gt, group in enumerate(cause["member_queries_per_gt"])
        if int(gt) == target_index
        for query in group
    }
    if nearest.intersection(members):
        raise ValueError("Native nearest and membership causes overlap")
    target_positive = target_nearest | target_member
    native_positive = [bool(value) for value in cause["native_positive"]]
    if len(native_positive) != query_count:
        raise ValueError("Native-positive axis differs")
    if any(
        native_positive[query] != (
            query in nearest or query in members
        )
        for query in range(query_count)
    ):
        raise ValueError("Native-positive vector differs from causes")
    other_positive = {
        query
        for query, value in enumerate(native_positive)
        if value and query not in target_positive
    }
    if target_positive & other_positive:
        raise ValueError("Target and other-GT positives overlap")
    return {
        "target_object_id": target,
        "target_index": target_index,
        "all_native_positive": {
            query for query, value in enumerate(native_positive) if value
        },
        "target_positive": target_positive,
        "target_nearest": target_nearest,
        "target_member": target_member,
        "other_gt_only": other_positive,
    }


def top_score_query(queries, scores):
    if not queries:
        return None
    return min(queries, key=lambda query: (-float(scores[query]), query))


def selection_row(queries, scores, ious):
    query = top_score_query(queries, scores)
    if query is None:
        return None
    return {
        "query": int(query),
        "score": float(scores[query]),
        "iou": float(ious[query]),
        "success": bool(float(ious[query]) > 0.5),
    }


def analyze_expression(row):
    if int(row.get("manifest_index", -1)) < 0:
        raise ValueError("Expression lacks a manifest index")
    cause = row.get("native_match_cause")
    if not isinstance(cause, dict):
        raise ValueError("Native matcher causes are missing")
    check_row(cause)
    sets = target_cause_sets(cause, row.get("target_object_id"))
    scores = [float(value) for value in row.get("scores", [])]
    ious = [float(value) for value in row.get("ious", [])]
    query_count = len(cause["sampled_pos"])
    if len(scores) != query_count or len(ious) != query_count:
        raise ValueError("Expression outcome axes differ")
    if any(not math.isfinite(value) for value in scores + ious):
        raise ValueError("Expression outcome contains nonfinite values")
    if any(value < 0.0 or value > 1.0 for value in ious):
        raise ValueError("Expression IoU is outside [0,1]")
    deployed = int(row.get("selected_query", -1))
    if deployed < 0 or deployed >= query_count:
        raise ValueError("Deployed query is outside the query axis")

    selections = {
        "deployed": {
            "query": deployed,
            "score": scores[deployed],
            "iou": ious[deployed],
            "success": ious[deployed] > 0.5,
        },
        "all_native_positive": selection_row(
            sets["all_native_positive"], scores, ious
        ),
        "target_positive": selection_row(
            sets["target_positive"], scores, ious
        ),
        "target_nearest": selection_row(
            sets["target_nearest"], scores, ious
        ),
        "target_member": selection_row(
            sets["target_member"], scores, ious
        ),
    }
    return {
        "manifest_index": int(row["manifest_index"]),
        "scene_id": str(row["scene"]),
        "ann_id": int(row["ann_id"]),
        "target_object_id": sets["target_object_id"],
        "query_count": query_count,
        "target_positive_queries": {
            "all": len(sets["target_positive"]),
            "nearest": len(sets["target_nearest"]),
            "member": len(sets["target_member"]),
            "other_gt_only": len(sets["other_gt_only"]),
        },
        "selections": selections,
        "target_positive_changed_from_deployed": (
            selections["target_positive"] is not None
            and selections["target_positive"]["query"] != deployed
        ),
        "target_positive_changed_from_native_positive": (
            selections["target_positive"] is not None
            and selections["all_native_positive"] is not None
            and selections["target_positive"]["query"]
            != selections["all_native_positive"]["query"]
        ),
    }


def scene_balanced(values_by_scene):
    groups = [values for values in values_by_scene.values() if values]
    if not groups:
        return None
    return sum(sum(group) / len(group) for group in groups) / len(groups)


def scene_bootstrap(values_by_scene, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED):
    groups = [values for values in values_by_scene.values() if values]
    if not groups:
        return None
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        selected = rng.choices(groups, k=len(groups))
        samples.append(
            sum(sum(group) / len(group) for group in selected) / len(groups)
        )
    samples.sort()
    return {
        "draws": draws,
        "seed": seed,
        "unit": "scene",
        "scene_count": len(groups),
        "point_estimate": scene_balanced(values_by_scene),
        "lo": samples[int(0.025 * (draws - 1))],
        "hi": samples[int(0.975 * (draws - 1))],
    }


def summarize_selector(rows, selector, draws=BOOTSTRAP_DRAWS):
    available = [
        (row, row["selections"][selector])
        for row in rows
        if row["selections"][selector] is not None
    ]
    if not available:
        return {
            "available": 0,
            "mean_iou": None,
            "scene_balanced_iou": None,
            "success_rate": None,
            "scene_balanced_success": None,
        }
    ious = [selection["iou"] for _, selection in available]
    successes = [float(selection["success"]) for _, selection in available]
    by_scene_iou = defaultdict(list)
    by_scene_success = defaultdict(list)
    for row, selection in available:
        by_scene_iou[row["scene_id"]].append(selection["iou"])
        by_scene_success[row["scene_id"]].append(float(selection["success"]))
    return {
        "available": len(available),
        "mean_iou": sum(ious) / len(ious),
        "scene_balanced_iou": scene_balanced(by_scene_iou),
        "success_rate": sum(successes) / len(successes),
        "scene_balanced_success": scene_balanced(by_scene_success),
        "scene_bootstrap_iou_95ci": scene_bootstrap(
            by_scene_iou, draws=draws
        ),
        "scene_bootstrap_success_95ci": scene_bootstrap(
            by_scene_success, draws=draws
        ),
    }


def paired_summary(rows, comparison, draws=BOOTSTRAP_DRAWS):
    pairs = []
    for row in rows:
        selections = row["selections"]
        left_name, right_name = comparison.split("_minus_")
        left = selections[left_name]
        right = selections[right_name]
        if left is None or right is None:
            continue
        pairs.append(
            (
                row["scene_id"],
                left["iou"] - right["iou"],
                float(left["success"]) - float(right["success"]),
            )
        )
    if not pairs:
        return {
            "available": 0,
            "mean_iou_difference": None,
            "scene_balanced_iou_difference": None,
            "mean_success_difference": None,
            "scene_balanced_success_difference": None,
        }
    by_scene_iou = defaultdict(list)
    by_scene_success = defaultdict(list)
    for scene, iou_difference, success_difference in pairs:
        by_scene_iou[scene].append(iou_difference)
        by_scene_success[scene].append(success_difference)
    return {
        "available": len(pairs),
        "mean_iou_difference": (
            sum(pair[1] for pair in pairs) / len(pairs)
        ),
        "scene_balanced_iou_difference": scene_balanced(by_scene_iou),
        "mean_success_difference": (
            sum(pair[2] for pair in pairs) / len(pairs)
        ),
        "scene_balanced_success_difference": scene_balanced(by_scene_success),
        "scene_bootstrap_iou_95ci": scene_bootstrap(
            by_scene_iou, draws=draws
        ),
        "scene_bootstrap_success_95ci": scene_bootstrap(
            by_scene_success, draws=draws
        ),
    }


def summarize(rows, draws=BOOTSTRAP_DRAWS):
    target_rows = [
        row for row in rows
        if row["selections"]["target_positive"] is not None
    ]
    query_counts = {
        "target_positive": 0,
        "target_nearest": 0,
        "target_member": 0,
        "other_gt_only": 0,
    }
    for row in rows:
        query_counts["target_positive"] += row["target_positive_queries"]["all"]
        query_counts["target_nearest"] += row["target_positive_queries"]["nearest"]
        query_counts["target_member"] += row["target_positive_queries"]["member"]
        query_counts["other_gt_only"] += row["target_positive_queries"]["other_gt_only"]
    return {
        "expressions": len(rows),
        "scenes": len({row["scene_id"] for row in rows}),
        "expressions_with_target_positive": len(target_rows),
        "query_cause_counts": query_counts,
        "rows_changed_from_deployed": sum(
            row["target_positive_changed_from_deployed"] for row in rows
        ),
        "rows_changed_from_all_native_positive": sum(
            row["target_positive_changed_from_native_positive"] for row in rows
        ),
        "selectors": {
            selector: summarize_selector(rows, selector, draws=draws)
            for selector in SELECTORS
        },
        "paired_comparisons": {
            comparison: paired_summary(rows, comparison, draws=draws)
            for comparison in PAIRED_COMPARISONS
        },
    }


def analyze(capture, draws=BOOTSTRAP_DRAWS):
    rows = [analyze_expression(row) for _, row in sorted(
        validate_capture(capture).items()
    )]
    return {"rows": rows, "summary": summarize(rows, draws=draws)}


def write_json(path, document):
    path = Path(path)
    if path.exists():
        raise ValueError("Output already exists: %s" % path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="ascii",
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--draws", type=int, default=BOOTSTRAP_DRAWS)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.draws <= 0:
        raise ValueError("Bootstrap draws must be positive")
    capture_path = Path(args.capture).resolve()
    capture = load_json(capture_path)
    result = analyze(capture, draws=args.draws)
    result.update(
        {
            "schema_version": 1,
            "contract": ANALYSIS_CONTRACT,
            "scope": (
                "CPU-only exact match-cause partition of the native M95 "
                "full-train capture. No model execution, training, native "
                "backward, resource measurement, admission or efficacy claim."
            ),
            "source_capture": {
                "path": str(capture_path),
                "sha256": file_sha256(capture_path),
                "producer_sha256": capture.get("producer_sha256"),
                "checkpoint_sha256": capture.get("checkpoint_sha256"),
            },
            "selector_contract": {
                "deployed": "native argmax query recorded by the capture",
                "all_native_positive": (
                    "oracle top-score query inside the full native-positive set"
                ),
                "target_positive": (
                    "oracle top-score query with a nearest or member cause "
                    "bound to the target object"
                ),
                "target_nearest": (
                    "oracle top-score query nearest to the target object"
                ),
                "target_member": (
                    "oracle top-score target-instance member query"
                ),
            },
            "admission": False,
            "native_backward_measured": False,
            "resources_measured": False,
            "not_evidence_of": [
                "admission",
                "native backward",
                "resource gate",
                "deployable selector",
                "deployable efficacy",
                "population effect",
                "novelty",
                "whole-mechanism benefit",
            ],
        }
    )
    write_json(args.output, result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
