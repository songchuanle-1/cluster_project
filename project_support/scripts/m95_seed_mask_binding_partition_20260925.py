"""Partition M95 native-negative selections by query-seed/mask binding.

This read-only CPU diagnostic tests whether deployed wrong-instance masks are
internally inconsistent with their own sampled query seed. It does not test a
selector or propose a training mechanism.
"""
import argparse
import hashlib
import json
from collections import Counter
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


def mask_contains(mask, index):
    if hasattr(mask, "tolist"):
        mask = mask.tolist()
    if not 0 <= index < len(mask):
        raise ValueError("Sampled seed index is out of range")
    return bool(mask[index])


def selected_wrong_instances(row):
    target = {int(value) for value in row["target_instances"]}
    overlaps = row.get("selected_mask_endpoints", {}).get("overlaps")
    if not isinstance(overlaps, list):
        raise ValueError("Selected mask endpoints are missing")
    return {
        int(overlap["instance"])
        for overlap in overlaps
        if float(overlap["iou"]) > 0.5 and int(overlap["instance"]) not in target
    }


def partition_query(row, artifact, query):
    labels = artifact["physical_instance_labels"]
    if hasattr(labels, "tolist"):
        labels = labels.tolist()
    seeds = row["sampled_seed_indices"]
    inverse = row["sample_inverse"]
    masks = artifact["query_masks"]
    if not labels or len(seeds) != EXPECTED_QUERIES:
        raise ValueError("Query seed or instance-label axis differs")
    if len(masks) != EXPECTED_QUERIES:
        raise ValueError("Query mask count differs")
    if len(masks[query]) != len(labels):
        raise ValueError("Query mask and instance-label axes differ")
    seed_index = int(seeds[query])
    if not 0 <= seed_index < len(inverse):
        raise ValueError("Sampled seed index is out of range")
    sampled_seed_index = int(inverse[seed_index])
    if not 0 <= sampled_seed_index < len(labels):
        raise ValueError("Sampled seed inverse is out of range")
    seed_instance = int(labels[sampled_seed_index])
    target = {int(value) for value in row["target_instances"]}
    wrong = selected_wrong_instances(row)
    return {
        "seed_index": seed_index,
        "sampled_seed_index": sampled_seed_index,
        "seed_instance": seed_instance,
        "seed_in_target": seed_instance in target,
        "seed_in_wrong_instance": seed_instance in wrong,
        "seed_is_background": seed_instance < 0,
        "seed_in_its_mask": mask_contains(masks[query], sampled_seed_index),
    }


def analyze_rows(rows, artifacts):
    all_query = Counter()
    mismatch = []
    for row in rows:
        scores = [float(value) for value in row["scores"]]
        if len(scores) != EXPECTED_QUERIES:
            raise ValueError("Expression query count differs")
        selected = int(row["selected_query"])
        if selected != top_score_query(scores):
            raise ValueError("Selected query differs from score argmax")
        index = int(row["manifest_index"])
        artifact = artifacts[index]
        for query in range(EXPECTED_QUERIES):
            result = partition_query(row, artifact, query)
            all_query["queries"] += 1
            all_query["seed_in_its_mask"] += int(result["seed_in_its_mask"])
            all_query["seed_in_target"] += int(result["seed_in_target"])

        if bool(row["native_positive"][selected]):
            continue
        selected_result = partition_query(row, artifact, selected)
        mismatch.append({
            "manifest_index": index,
            "scene_id": str(row["scene"]),
            "selected_query": selected,
            "selected_iou": float(row["ious"][selected]),
            "wrong_instance_count": len(selected_wrong_instances(row)),
            **selected_result,
        })

    mismatch_counts = Counter()
    for result in mismatch:
        mismatch_counts["rows"] += 1
        mismatch_counts["seed_in_its_mask"] += int(result["seed_in_its_mask"])
        mismatch_counts["seed_in_target"] += int(result["seed_in_target"])
        mismatch_counts["seed_in_wrong_instance"] += int(
            result["seed_in_wrong_instance"]
        )
        mismatch_counts["seed_is_background"] += int(result["seed_is_background"])
        mismatch_counts["seed_not_target_or_wrong"] += int(
            not result["seed_in_target"]
            and not result["seed_in_wrong_instance"]
            and not result["seed_is_background"]
        )
        if result["seed_in_wrong_instance"] and result["seed_in_its_mask"]:
            mismatch_counts["follows_wrong_instance_seed"] += 1
        if not result["seed_in_its_mask"]:
            mismatch_counts["mask_excludes_own_seed"] += 1

    return {
        "all_queries": {
            "queries": all_query["queries"],
            "seed_in_its_mask": all_query["seed_in_its_mask"],
            "seed_in_its_mask_rate": (
                all_query["seed_in_its_mask"] / all_query["queries"]
            ),
            "seed_in_target": all_query["seed_in_target"],
        },
        "native_negative_selected": {
            **dict(sorted(mismatch_counts.items())),
            "seed_in_its_mask_rate": (
                mismatch_counts["seed_in_its_mask"] / mismatch_counts["rows"]
                if mismatch_counts["rows"] else None
            ),
            "seed_in_wrong_instance_rate": (
                mismatch_counts["seed_in_wrong_instance"] / mismatch_counts["rows"]
                if mismatch_counts["rows"] else None
            ),
        },
        "rows": mismatch,
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
    return {
        "capture_sha256": actual_sha256,
        "summary": analyze_rows(rows, artifacts),
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
    return parser.parse_args()


def main():
    args = parse_args()
    result = analyze_capture(args.capture, capture_dir=args.capture_dir)
    result.update({
        "schema_version": 1,
        "contract": "m95_seed_mask_binding_partition_v1",
        "scope": (
            "Read-only CPU partition of the completed exact M95 capture. "
            "No selector, mechanism, training, native backward, resource, "
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
