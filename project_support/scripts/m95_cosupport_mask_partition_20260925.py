"""Partition the exact M95 all-native-positive oracle by mask co-support.

The exact native cause partition showed that the target-positive-only oracle
does not outperform the all-native-positive oracle. This CPU-only diagnostic
tests a distinct explanation: whether the all-native-positive advantage comes
from other-object positive queries whose predicted masks overlap the target.

It is read-only diagnostic evidence. It does not select a deployable query,
train a model, measure resources, or establish an admissible mechanism.
"""
import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

try:
    import torch
except ImportError:
    torch = None


EXPECTED_MANIFEST_SHA256 = (
    "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
)
EXPECTED_CHECKPOINT_SHA256 = (
    "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
)
EXPECTED_PRODUCER_SHA256 = (
    "206c594d8c5219c6e249d89f7cb91815467bd443a030bc8bbd76d457de0b485a"
)
EXPECTED_CAPTURE_MODE = "full_train_scan"
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


def target_cause_sets(cause, target_object_id):
    object_ids = [int(value) for value in cause["object_ids"]]
    target = int(target_object_id)
    matches = [index for index, value in enumerate(object_ids) if value == target]
    if len(matches) != 1:
        raise ValueError("Native target object binding differs")
    target_index = matches[0]
    nearest = {
        query
        for query, gt in enumerate(cause["nearest_query_per_gt"])
        if int(gt) == target_index
    }
    members = {
        query
        for gt, group in enumerate(cause["member_queries_per_gt"])
        if gt == target_index
        for query in group
    }
    all_positive = {
        query
        for query, value in enumerate(cause["native_positive"])
        if bool(value)
    }
    return {
        "all": all_positive,
        "nearest": nearest,
        "member": members,
        "target": nearest | members,
    }


def selection_class(query, cause_sets):
    if query in cause_sets["nearest"]:
        return "target_nearest"
    if query in cause_sets["member"]:
        return "target_member"
    if query in cause_sets["all"]:
        return "other_gt_only"
    raise ValueError("Selected query is outside the native-positive set")


def mask_overlap(mask, target_union):
    if torch is not None and hasattr(mask, "to"):
        mask = mask.to(torch.bool)
        target_union = target_union.to(torch.bool)
    if hasattr(mask, "tolist"):
        mask = mask.tolist()
    if hasattr(target_union, "tolist"):
        target_union = target_union.tolist()
    mask = [bool(value) for value in mask]
    target_union = [bool(value) for value in target_union]
    if len(mask) != len(target_union):
        raise ValueError("Query mask and target union differ")
    overlap = sum(left and right for left, right in zip(mask, target_union))
    union = sum(left or right for left, right in zip(mask, target_union))
    mask_count = sum(mask)
    return {
        "overlap_superpoints": overlap,
        "mask_superpoints": mask_count,
        "overlap_fraction": overlap / max(mask_count, 1),
        "mask_iou": overlap / max(union, 1),
    }


def scene_balanced(values_by_scene):
    groups = [values for values in values_by_scene.values() if values]
    if not groups:
        return None
    return sum(sum(group) / len(group) for group in groups) / len(groups)


def bootstrap(values_by_scene, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED):
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


def summarize_rows(rows, draws=BOOTSTRAP_DRAWS):
    by_class = defaultdict(list)
    for row in rows:
        by_class[row["selected_class"]].append(row)

    class_summary = {}
    for name, selected in sorted(by_class.items()):
        by_scene_success = defaultdict(list)
        by_scene_iou = defaultdict(list)
        by_scene_overlap = defaultdict(list)
        by_scene_mask_iou = defaultdict(list)
        for row in selected:
            scene = row["scene_id"]
            by_scene_success[scene].append(float(row["selected_success"]))
            by_scene_iou[scene].append(float(row["selected_iou"]))
            by_scene_overlap[scene].append(float(row["overlap_fraction"]))
            by_scene_mask_iou[scene].append(float(row["mask_iou"]))
        class_summary[name] = {
            "rows": len(selected),
            "mean_iou": sum(row["selected_iou"] for row in selected) / len(selected),
            "success_rate": sum(
                row["selected_success"] for row in selected
            ) / len(selected),
            "scene_balanced_iou": scene_balanced(by_scene_iou),
            "scene_balanced_success": scene_balanced(by_scene_success),
            "scene_balanced_overlap_fraction": scene_balanced(by_scene_overlap),
            "scene_balanced_mask_iou": scene_balanced(by_scene_mask_iou),
            "mask_iou_above_half": sum(
                row["mask_iou"] > 0.5 for row in selected
            ),
            "scene_bootstrap_iou_95ci": bootstrap(by_scene_iou, draws=draws),
            "scene_bootstrap_success_95ci": bootstrap(
                by_scene_success, draws=draws
            ),
            "scene_bootstrap_mask_iou_95ci": bootstrap(
                by_scene_mask_iou, draws=draws
            ),
        }

    changed = [
        row for row in rows
        if row["target_positive_query"] is not None
        and row["selected_query"] != row["target_positive_query"]
    ]
    changed_iou = defaultdict(list)
    changed_success = defaultdict(list)
    for row in changed:
        scene = row["scene_id"]
        changed_iou[scene].append(row["iou_delta_vs_target_positive"])
        changed_success[scene].append(row["success_delta_vs_target_positive"])
    return {
        "rows": len(rows),
        "scenes": len({row["scene_id"] for row in rows}),
        "classes": class_summary,
        "changed_from_target_positive": {
            "rows": len(changed),
            "improved_iou": sum(
                row["iou_delta_vs_target_positive"] > 0 for row in changed
            ),
            "worsened_iou": sum(
                row["iou_delta_vs_target_positive"] < 0 for row in changed
            ),
            "mean_iou_delta": (
                sum(
                    row["iou_delta_vs_target_positive"] for row in changed
                ) / len(changed)
                if changed else None
            ),
            "scene_balanced_iou_delta": scene_balanced(changed_iou),
            "scene_balanced_success_delta": scene_balanced(changed_success),
            "scene_bootstrap_iou_delta_95ci": bootstrap(
                changed_iou, draws=draws
            ),
            "scene_bootstrap_success_delta_95ci": bootstrap(
                changed_success, draws=draws
            ),
        },
    }


def validate_capture(capture):
    if capture.get("capture_mode") != EXPECTED_CAPTURE_MODE:
        raise ValueError("Capture is not the exact full-train scan")
    if capture.get("producer_sha256") != EXPECTED_PRODUCER_SHA256:
        raise ValueError("Capture producer differs from the frozen contract")
    if capture.get("checkpoint_sha256") != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError("Capture checkpoint differs from M95")
    if capture.get("manifest", {}).get("sha256") != EXPECTED_MANIFEST_SHA256:
        raise ValueError("Capture manifest differs from the frozen contract")
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
    by_index = {int(row["manifest_index"]): row for row in rows}
    if set(by_index) != set(range(EXPECTED_ROWS)):
        raise ValueError("Capture manifest coverage differs")
    return by_index


def load_artifacts(capture, capture_dir):
    if torch is None:
        raise RuntimeError("PyTorch is required to load feature artifacts")
    entries = capture.get("feature_artifacts")
    if not isinstance(entries, list):
        raise ValueError("Capture lacks feature artifacts")
    artifacts = {}
    for entry in entries:
        path = capture_dir / str(entry["path"])
        if file_sha256(path) != entry["sha256"]:
            raise ValueError("Feature artifact hash differs")
        loaded = torch.load(path, map_location="cpu", weights_only=False)
        if len(loaded) != int(entry["rows"]):
            raise ValueError("Feature artifact row count differs")
        for artifact in loaded:
            index = int(artifact["manifest_index"])
            if index in artifacts:
                raise ValueError("Duplicate feature artifact row")
            if artifact.get("artifact_contract") != "m95_manifest_native_query_artifact_v1":
                raise ValueError("Feature artifact contract differs")
            artifacts[index] = artifact
    if set(artifacts) != set(range(EXPECTED_ROWS)):
        raise ValueError("Feature artifact coverage differs")
    return artifacts


def analyze_capture(capture_path, capture_dir=None, draws=BOOTSTRAP_DRAWS):
    capture_path = Path(capture_path).resolve()
    capture_dir = Path(capture_dir or capture_path.parent).resolve()
    capture = load_json(capture_path)
    rows = validate_capture(capture)
    artifacts = load_artifacts(capture, capture_dir)
    selected_rows = []
    for index, row in sorted(rows.items()):
        cause = row.get("native_match_cause")
        if not isinstance(cause, dict):
            raise ValueError("Native match causes are missing")
        scores = [float(value) for value in row["scores"]]
        ious = [float(value) for value in row["ious"]]
        cause_sets = target_cause_sets(cause, row["target_object_id"])
        if len(scores) != len(cause["native_positive"]) or len(ious) != len(scores):
            raise ValueError("Expression outcome axes differ")
        selected_query = top_score_query(cause_sets["all"], scores)
        target_positive_query = top_score_query(cause_sets["target"], scores)
        if selected_query is None:
            raise ValueError("Expression lacks a native-positive query")
        artifact = artifacts[index]
        overlaps = mask_overlap(
            artifact["query_masks"][selected_query],
            artifact["target_union"],
        )
        selected_rows.append({
            "manifest_index": index,
            "scene_id": str(row["scene"]),
            "selected_query": selected_query,
            "selected_class": selection_class(selected_query, cause_sets),
            "selected_score": scores[selected_query],
            "selected_iou": ious[selected_query],
            "selected_success": ious[selected_query] > 0.5,
            "target_positive_query": target_positive_query,
            "iou_delta_vs_target_positive": (
                ious[selected_query] - ious[target_positive_query]
                if target_positive_query is not None else None
            ),
            "success_delta_vs_target_positive": (
                float(ious[selected_query] > 0.5)
                - float(ious[target_positive_query] > 0.5)
                if target_positive_query is not None else None
            ),
            **overlaps,
        })
    return {
        "capture_sha256": file_sha256(capture_path),
        "rows": selected_rows,
        "summary": summarize_rows(selected_rows, draws=draws),
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
    parser.add_argument("--capture-dir")
    parser.add_argument("--output", required=True)
    parser.add_argument("--draws", type=int, default=BOOTSTRAP_DRAWS)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.draws <= 0:
        raise ValueError("Bootstrap draws must be positive")
    result = analyze_capture(
        args.capture,
        capture_dir=args.capture_dir,
        draws=args.draws,
    )
    result.update({
        "schema_version": 1,
        "contract": "m95_cosupport_mask_partition_v1",
        "scope": (
            "Read-only CPU partition of the completed exact M95 capture. "
            "No training, deployable selector, native backward, resources, "
            "novelty claim, admission, or efficacy claim."
        ),
        "admission": False,
        "native_backward_measured": False,
        "resources_measured": False,
        "not_evidence_of": [
            "admission",
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
