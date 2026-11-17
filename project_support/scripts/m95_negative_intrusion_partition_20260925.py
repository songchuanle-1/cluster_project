"""Partition M95 deployed-selection failures caused by native-negative queries.

This is a read-only CPU diagnostic over the frozen exact capture. It tests
whether the remaining observable mismatch contains a new causal unit or only
restates the already-closed referent classification/ranking family.
"""
import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


EXPECTED_CAPTURE_SHA256 = (
    "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"
)
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
BOOTSTRAP_DRAWS = 10000
BOOTSTRAP_SEED = 1999


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def top_score_query(queries, scores):
    if not queries:
        return None
    return min(queries, key=lambda query: (-float(scores[query]), query))


def selected_wrong_instance(row, target_instances):
    target = {int(value) for value in target_instances}
    overlaps = row.get("selected_mask_endpoints", {}).get("overlaps")
    if not isinstance(overlaps, list):
        raise ValueError("Selected mask endpoints are missing")
    return any(
        int(overlap["instance"]) not in target
        and float(overlap["iou"]) > 0.5
        for overlap in overlaps
    )


def classify_selected(row):
    selected = int(row["selected_query"])
    target_iou = float(row["ious"][selected])
    wrong = selected_wrong_instance(row, row["target_instances"])
    if target_iou > 0.5:
        category = "target_false_negative"
    elif wrong:
        category = "wrong_instance"
    else:
        category = "neither_target_nor_wrong_instance"
    return {
        "category": category,
        "selected_target_iou_above_half": target_iou > 0.5,
        "selected_wrong_instance_iou_above_half": wrong,
    }


def scene_balanced(values_by_scene):
    groups = [values for values in values_by_scene.values() if values]
    if not groups:
        return None
    return sum(sum(group) / len(group) for group in groups) / len(groups)


def bootstrap_scene(values_by_scene, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED):
    groups = [values for values in values_by_scene.values() if values]
    if not groups:
        return None
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        chosen = rng.choices(groups, k=len(groups))
        samples.append(
            sum(sum(group) / len(group) for group in chosen) / len(groups)
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


def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return None
    return ordered[min(len(ordered) - 1, int(fraction * (len(ordered) - 1)))]


def analyze_rows(rows, draws=BOOTSTRAP_DRAWS):
    mismatch = []
    for row in rows:
        scores = [float(value) for value in row["scores"]]
        ious = [float(value) for value in row["ious"]]
        positive = [
            index for index, value in enumerate(row["native_positive"]) if value
        ]
        if not scores or len(scores) != len(ious) or len(scores) != len(
                row["native_positive"]):
            raise ValueError("Expression score, IoU, and positive axes differ")
        selected = int(row["selected_query"])
        if selected != top_score_query(range(len(scores)), scores):
            raise ValueError("Selected query differs from score argmax")
        if selected in positive:
            continue
        best_positive = top_score_query(positive, scores)
        if best_positive is None:
            raise ValueError("Mismatched expression lacks a native-positive query")
        ordered = sorted(range(len(scores)), key=lambda query: (-scores[query], query))
        classification = classify_selected(row)
        mismatch.append({
            "manifest_index": int(row["manifest_index"]),
            "scene_id": str(row["scene"]),
            "selected_query": selected,
            "best_positive_query": best_positive,
            "selected_score": scores[selected],
            "best_positive_score": scores[best_positive],
            "selected_minus_positive_score": scores[selected] - scores[best_positive],
            "positive_score_rank": ordered.index(best_positive) + 1,
            "selected_iou": ious[selected],
            "best_positive_iou": ious[best_positive],
            "positive_minus_selected_iou": ious[best_positive] - ious[selected],
            "positive_minus_selected_success": (
                float(ious[best_positive] > 0.5) - float(ious[selected] > 0.5)
            ),
            "selected_seed_inside_target": bool(row["seed_inside"][selected]),
            "best_positive_seed_inside_target": bool(
                row["seed_inside"][best_positive]
            ),
            "any_positive_seed_inside_target": any(
                bool(row["seed_inside"][query]) for query in positive
            ),
            **classification,
        })

    categories = Counter(row["category"] for row in mismatch)
    by_scene_iou = defaultdict(list)
    by_scene_success = defaultdict(list)
    by_category_iou = defaultdict(list)
    by_category_success = defaultdict(list)
    for row in mismatch:
        scene = row["scene_id"]
        by_scene_iou[scene].append(row["positive_minus_selected_iou"])
        by_scene_success[scene].append(row["positive_minus_selected_success"])
        by_category_iou[row["category"]].append(row["selected_iou"])
        by_category_success[row["category"]].append(
            float(row["selected_iou"] > 0.5)
        )

    category_summary = {}
    for category, count in sorted(categories.items()):
        category_summary[category] = {
            "rows": count,
            "mean_selected_iou": (
                sum(by_category_iou[category]) / len(by_category_iou[category])
            ),
            "success_rate": (
                sum(by_category_success[category])
                / len(by_category_success[category])
            ),
        }

    selected_ious = [row["selected_iou"] for row in mismatch]
    score_margins = [row["selected_minus_positive_score"] for row in mismatch]
    positive_ranks = [row["positive_score_rank"] for row in mismatch]
    return {
        "rows": {
            "expressions": len(rows),
            "scenes": len({str(row["scene"]) for row in rows}),
            "native_negative_deployed_mismatches": len(mismatch),
        },
        "categories": category_summary,
        "score_rank": {
            "counts": dict(sorted(Counter(positive_ranks).items())),
            "median_best_positive_rank": quantile(positive_ranks, 0.5),
            "p90_best_positive_rank": quantile(positive_ranks, 0.9),
        },
        "selected_negative": {
            "mean_iou": sum(selected_ious) / len(selected_ious),
            "median_iou": quantile(selected_ious, 0.5),
            "mean_score_margin_over_best_positive": (
                sum(score_margins) / len(score_margins)
            ),
            "median_score_margin_over_best_positive": quantile(score_margins, 0.5),
            "p90_score_margin_over_best_positive": quantile(score_margins, 0.9),
        },
        "seed_location": {
            "selected_seed_inside_target": sum(
                row["selected_seed_inside_target"] for row in mismatch
            ),
            "best_positive_seed_inside_target": sum(
                row["best_positive_seed_inside_target"] for row in mismatch
            ),
            "any_positive_seed_inside_target": sum(
                row["any_positive_seed_inside_target"] for row in mismatch
            ),
        },
        "positive_minus_selected": {
            "mean_iou": (
                sum(row["positive_minus_selected_iou"] for row in mismatch)
                / len(mismatch)
            ),
            "mean_success": (
                sum(row["positive_minus_selected_success"] for row in mismatch)
                / len(mismatch)
            ),
            "scene_balanced_iou": scene_balanced(by_scene_iou),
            "scene_balanced_success": scene_balanced(by_scene_success),
            "scene_bootstrap_iou_95ci": bootstrap_scene(
                by_scene_iou, draws=draws
            ),
            "scene_bootstrap_success_95ci": bootstrap_scene(
                by_scene_success, draws=draws
            ),
        },
        "mismatch_rows": mismatch,
    }


def validate_capture(capture):
    if capture.get("producer_sha256") != EXPECTED_PRODUCER_SHA256:
        raise ValueError("Capture producer differs from frozen contract")
    if capture.get("checkpoint_sha256") != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError("Capture checkpoint differs from M95")
    if capture.get("manifest", {}).get("sha256") != EXPECTED_MANIFEST_SHA256:
        raise ValueError("Capture manifest differs from frozen contract")
    if capture.get("capture_mode") != "full_train_scan":
        raise ValueError("Capture is not the exact full-train scan")
    for key in (
        "native_capture_completed",
        "native_match_cause_completed",
        "identity_query_completed",
    ):
        if capture.get(key) is not True:
            raise ValueError("Capture completion flag differs: %s" % key)
    rows = capture.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_ROWS:
        raise ValueError("Capture does not contain 256 rows")
    indices = [int(row["manifest_index"]) for row in rows]
    if sorted(indices) != list(range(EXPECTED_ROWS)):
        raise ValueError("Capture manifest coverage differs")
    return rows


def analyze_capture(capture_path, draws=BOOTSTRAP_DRAWS):
    capture_path = Path(capture_path).resolve()
    actual_sha256 = file_sha256(capture_path)
    if actual_sha256 != EXPECTED_CAPTURE_SHA256:
        raise ValueError("Capture SHA256 differs from frozen contract")
    capture = load_json(capture_path)
    rows = validate_capture(capture)
    return {
        "capture_sha256": actual_sha256,
        "summary": analyze_rows(rows, draws=draws),
    }


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
    result = analyze_capture(args.capture, draws=args.draws)
    result.update({
        "schema_version": 1,
        "contract": "m95_negative_intrusion_partition_v1",
        "scope": (
            "Read-only CPU partition of the completed exact M95 capture. "
            "No model execution, training, deployable selector, native "
            "backward, resource, novelty, admission, or efficacy claim."
        ),
        "admission": False,
        "native_backward_measured": False,
        "resources_measured": False,
        "not_evidence_of": [
            "admission",
            "new causal mechanism",
            "deployable selector",
            "deployable efficacy",
            "novelty",
            "whole-mechanism benefit",
        ],
    })
    write_json(args.output, result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
