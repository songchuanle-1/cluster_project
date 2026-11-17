"""Measure duplicate-mask dominance in the frozen M95 exact capture.

The diagnostic tests whether deployed wrong-instance failures are supported by
multiple redundant high-score masks rather than by one isolated score error.
It is read-only and does not establish an admission or a training mechanism.
"""
import argparse
import hashlib
import json
import math
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
EXPECTED_QUERIES = 128
EXPECTED_ARTIFACT_CONTRACT = "m95_manifest_native_query_artifact_v1"
DUPLICATE_IOU = 0.5
TARGET_IOU = 0.5


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def top_score_query(scores):
    if not scores:
        raise ValueError("Expression has no queries")
    return min(range(len(scores)), key=lambda query: (-float(scores[query]), query))


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


def load_artifacts(capture, capture_dir):
    entries = capture.get("feature_artifacts")
    if not isinstance(entries, list):
        raise ValueError("Capture lacks feature artifacts")
    artifacts = {}
    for entry in entries:
        path = Path(capture_dir) / str(entry["path"])
        if file_sha256(path) != entry["sha256"]:
            raise ValueError("Feature artifact hash differs")
        loaded = __import__("torch").load(
            path, map_location="cpu", weights_only=False
        )
        if len(loaded) != int(entry["rows"]):
            raise ValueError("Feature artifact row count differs")
        for artifact in loaded:
            index = int(artifact["manifest_index"])
            if index in artifacts:
                raise ValueError("Duplicate feature artifact row")
            if artifact.get("artifact_contract") != EXPECTED_ARTIFACT_CONTRACT:
                raise ValueError("Feature artifact contract differs")
            artifacts[index] = artifact
    if set(artifacts) != set(range(EXPECTED_ROWS)):
        raise ValueError("Feature artifact coverage differs")
    return artifacts


def iou(mask, target):
    if len(mask) != len(target):
        raise ValueError("Mask and target axes differ")
    intersection = 0
    union = 0
    for value, truth in zip(mask, target):
        selected = bool(value)
        expected = bool(truth)
        intersection += selected and expected
        union += selected or expected
    return 0.0 if union == 0 else intersection / union


def duplicate_mask_summary(masks, scores, target, selected, target_iou_threshold=TARGET_IOU):
    """Return score-ranked competition around the deployed query."""
    if len(masks) != len(scores):
        raise ValueError("Query mask and score axes differ")
    if not 0 <= selected < len(masks):
        raise ValueError("Selected query is out of range")

    try:
        torch = __import__("torch")
    except ImportError:
        torch = None
    if torch is not None and torch.is_tensor(masks):
        masks = masks.bool()
        target = torch.as_tensor(target, dtype=torch.bool, device=masks.device)
        if masks.ndim != 2 or masks.shape[1] != target.numel():
            raise ValueError("Query mask and target axes differ")
        selected_mask = masks[selected]
        intersections = (masks & target.unsqueeze(0)).sum(dim=1)
        unions = (masks | target.unsqueeze(0)).sum(dim=1)
        target_ious = torch.where(
            unions > 0,
            intersections.float() / unions.clamp_min(1),
            torch.zeros_like(intersections, dtype=torch.float32),
        )
        duplicate_intersections = (
            masks & selected_mask.unsqueeze(0)
        ).sum(dim=1)
        duplicate_unions = (
            masks | selected_mask.unsqueeze(0)
        ).sum(dim=1)
        duplicate_ious = torch.where(
            duplicate_unions > 0,
            duplicate_intersections.float() / duplicate_unions.clamp_min(1),
            torch.zeros_like(duplicate_intersections, dtype=torch.float32),
        )
        duplicate_mask = duplicate_ious > DUPLICATE_IOU
        duplicate_mask[selected] = False
        target_mask = target_ious > target_iou_threshold
        duplicate_queries = duplicate_mask.nonzero(as_tuple=False).flatten().tolist()
        target_queries = target_mask.nonzero(as_tuple=False).flatten().tolist()
        selected_target_iou = float(target_ious[selected].item())
    else:
        selected_mask = masks[selected]
        selected_target_iou = iou(selected_mask, target)
        duplicate_queries = []
        target_queries = []
        for query, mask in enumerate(masks):
            if query != selected and iou(mask, selected_mask) > DUPLICATE_IOU:
                duplicate_queries.append(query)
            if iou(mask, target) > target_iou_threshold:
                target_queries.append(query)

    if not target_queries:
        best_target = None
        target_above_selected = []
        duplicates_above_target = []
        duplicate_target_matches = []
    else:
        best_target = max(
            target_queries, key=lambda query: (float(scores[query]), -query)
        )
        target_score = float(scores[best_target])
        selected_score = float(scores[selected])
        target_above_selected = [
            query
            for query in target_queries
            if float(scores[query]) > selected_score
        ]
        duplicates_above_target = [
            query
            for query in duplicate_queries
            if float(scores[query]) > target_score
        ]
        duplicate_target_matches = [
            query
            for query in duplicate_queries
            if iou(masks[query], target) > target_iou_threshold
        ]

    duplicate_score = sum(float(scores[query]) for query in duplicate_queries)
    target_score = sum(float(scores[query]) for query in target_queries)
    return {
        "selected_target_iou": selected_target_iou,
        "duplicate_query_count": len(duplicate_queries),
        "target_query_count": len(target_queries),
        "duplicates_above_best_target": len(duplicates_above_target),
        "target_queries_above_selected": len(target_above_selected),
        "duplicate_target_matches": len(duplicate_target_matches),
        "best_target_query": best_target,
        "duplicate_score_mass": duplicate_score,
        "target_score_mass": target_score,
        "duplicate_to_target_score_ratio": (
            None if target_score == 0 else duplicate_score / target_score
        ),
    }


def mean(values):
    values = list(values)
    return None if not values else sum(values) / len(values)


def median(values):
    values = sorted(float(value) for value in values)
    if not values:
        return None
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2


def summarize_rows(rows):
    failures = [row for row in rows if row["failed"]]
    successes = [row for row in rows if not row["failed"]]
    with_target = [row for row in failures if row["target_query_count"] > 0]
    with_duplicate = [row for row in failures if row["duplicate_query_count"] > 0]
    summary = {
        "rows": len(rows),
        "failed_rows": len(failures),
        "successful_rows": len(successes),
        "failed_with_target_query": len(with_target),
        "failed_with_duplicate_query": len(with_duplicate),
        "successful_with_target_query": sum(
            row["target_query_count"] > 0 for row in successes
        ),
        "successful_with_duplicate_query": sum(
            row["duplicate_query_count"] > 0 for row in successes
        ),
        "failures_with_duplicate_and_target": sum(
            row["duplicate_query_count"] > 0 and row["target_query_count"] > 0
            for row in failures
        ),
        "failures_with_duplicate_above_best_target": sum(
            row["duplicates_above_best_target"] > 0 for row in failures
        ),
        "failures_with_target_above_selected": sum(
            row["target_queries_above_selected"] > 0 for row in failures
        ),
        "failures_with_duplicate_target_match": sum(
            row["duplicate_target_matches"] > 0 for row in failures
        ),
    }
    summary["successes"] = {
        "duplicate_query_count_mean": mean(
            row["duplicate_query_count"] for row in successes
        ),
        "duplicate_query_count_median": median(
            row["duplicate_query_count"] for row in successes
        ),
        "target_query_count_mean": mean(
            row["target_query_count"] for row in successes
        ),
        "target_query_count_median": median(
            row["target_query_count"] for row in successes
        ),
        "duplicates_above_best_target_mean": mean(
            row["duplicates_above_best_target"] for row in successes
        ),
        "target_queries_above_selected_mean": mean(
            row["target_queries_above_selected"] for row in successes
        ),
    }
    for scope, selected_rows in (("failures", failures), ("failures_with_target", with_target)):
        summary[scope] = {
            "duplicate_query_count_mean": mean(
                row["duplicate_query_count"] for row in selected_rows
            ),
            "duplicate_query_count_median": median(
                row["duplicate_query_count"] for row in selected_rows
            ),
            "target_query_count_mean": mean(
                row["target_query_count"] for row in selected_rows
            ),
            "target_query_count_median": median(
                row["target_query_count"] for row in selected_rows
            ),
            "duplicates_above_best_target_mean": mean(
                row["duplicates_above_best_target"] for row in selected_rows
            ),
            "target_queries_above_selected_mean": mean(
                row["target_queries_above_selected"] for row in selected_rows
            ),
        }
    return summary


def analyze_rows(rows, artifacts):
    results = []
    for row in rows:
        index = int(row["manifest_index"])
        artifact = artifacts[index]
        scores = [float(value) for value in row["scores"]]
        if len(scores) != EXPECTED_QUERIES:
            raise ValueError("Expression query count differs")
        selected = int(row["selected_query"])
        if selected != top_score_query(scores):
            raise ValueError("Selected query differs from score argmax")

        masks = artifact["query_masks"]
        target = artifact["target_union"]
        if len(masks) != EXPECTED_QUERIES:
            raise ValueError("Query mask count differs")
        if len(target) != len(artifact["physical_instance_labels"]):
            raise ValueError("Target and physical-label axes differ")
        if any(len(mask) != len(target) for mask in masks):
            raise ValueError("Query mask and target axes differ")

        summary = duplicate_mask_summary(masks, scores, target, selected)
        capture_iou = float(row["ious"][selected])
        if not math.isclose(
            capture_iou,
            summary["selected_target_iou"],
            abs_tol=1e-7,
        ):
            raise ValueError("Capture and artifact selected IoU differ")
        results.append({
            "manifest_index": index,
            "scene_id": str(row["scene"]),
            "selected_query": selected,
            "selected_iou": capture_iou,
            "native_positive": bool(row["native_positive"][selected]),
            "failed": capture_iou <= TARGET_IOU,
            **summary,
        })
    return {
        "summary": summarize_rows(results),
        "rows": results,
    }


def analyze_capture(capture_path, capture_dir=None):
    capture_path = Path(capture_path).resolve()
    capture_dir = Path(capture_dir or capture_path.parent).resolve()
    actual_sha256 = file_sha256(capture_path)
    if actual_sha256 != EXPECTED_CAPTURE_SHA256:
        raise ValueError("Capture SHA256 differs from frozen contract")
    capture = load_json(capture_path)
    rows = validate_capture(capture)
    artifacts = load_artifacts(capture, capture_dir)
    result = analyze_rows(rows, artifacts)
    result["capture_sha256"] = actual_sha256
    return result


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
    parser.add_argument("--capture-dir")
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    result = analyze_capture(args.capture, capture_dir=args.capture_dir)
    result.update({
        "schema_version": 1,
        "contract": "m95_duplicate_mask_dominance_v1",
        "scope": (
            "Read-only CPU diagnostic over the frozen exact M95 capture. "
            "No selector, model change, training, native backward, resource, "
            "novelty, admission, or efficacy claim."
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
