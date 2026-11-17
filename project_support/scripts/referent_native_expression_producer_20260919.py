"""Project native M95 capture rows into the frozen referent expression contract.

This CPU-only producer binds every registry-eligible expression to its native
observation by physical identity, preserves the native query order, and converts
confidence values into the predeclared lower-is-better cost axes. Target-mask
IoU is an oracle endpoint, not target-independent objectness. Missing coverage,
control scores or identity mismatches fail closed.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from referent_object_rank_capture_20260919 import file_sha256, stable_sha256


SCHEMA_VERSION = 1
MODEL_CLASS = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
OBJECTNESS_SEMANTICS = "target_independent_objectness_probability"
FROZEN_CAPTURE_PRODUCER_FILES = (
    "native_frozen_capture_20260916.py",
    "frozen_capture_contract_20260916.py",
    "hierarchical_partition_contract_20260916.py",
    "native_endpoint_capture_20260916.py",
    "native_support_capture_v2_20260916.py",
    "capture_support_20260916.py",
    "physical_mask_endpoints_20260916.py",
)


def frozen_capture_producer_sha256():
    """Return the aggregate hash written by the frozen native capture entrypoint."""
    script_dir = Path(__file__).resolve().parent
    payload = b"".join(
        (script_dir / name).read_bytes()
        for name in FROZEN_CAPTURE_PRODUCER_FILES
    )
    return hashlib.sha256(payload).hexdigest()


def _require_hash(value, field, length=64):
    if not isinstance(value, str) or len(value) != length:
        raise ValueError("Invalid hash field: " + field)
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError("Invalid hash field: " + field) from exc
    return value.lower()


def _probability(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Numeric probability required: " + field)
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError("Probability outside [0,1]: " + field)
    return value


def _identity_integer(value):
    if isinstance(value, bool):
        raise ValueError("Boolean physical identity")
    if isinstance(value, int) and value >= 0:
        return value
    if (
        isinstance(value, str)
        and value
        and value.isascii()
        and value.isdigit()
        and str(int(value)) == value
    ):
        return int(value)
    raise ValueError("Noncanonical physical identity")


def _physical_key_from_registry(row):
    order = row.get("dataset_order")
    if not isinstance(order, dict):
        raise ValueError("Registry dataset order is missing")
    scene = row.get("scene")
    if not isinstance(scene, str) or not scene:
        raise ValueError("Registry scene is missing")
    try:
        ann_id = str(_identity_integer(row.get("ann_id")))
        dataset_index = _identity_integer(order.get("step"))
        expression_slot = _identity_integer(order.get("expression_slot"))
    except (TypeError, ValueError) as exc:
        raise ValueError("Registry physical identity is invalid") from exc
    return scene, ann_id, dataset_index, expression_slot


def _physical_key_from_capture(row):
    scene = row.get("scene")
    if not isinstance(scene, str) or not scene:
        raise ValueError("Capture scene is missing")
    try:
        ann_id = str(_identity_integer(row.get("ann_id")))
        dataset_index = _identity_integer(row.get("dataset_index"))
        expression_slot = _identity_integer(row.get("expression_slot"))
    except (TypeError, ValueError) as exc:
        raise ValueError("Capture physical identity is invalid") from exc
    return scene, ann_id, dataset_index, expression_slot


def _validate_registry(registry):
    if registry.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported registry schema")
    rows = registry.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Registry rows are missing")
    if registry.get("registry_sha256") != stable_sha256(rows):
        raise ValueError("Registry content hash mismatch")

    indexed = {}
    for row in rows:
        key = _physical_key_from_registry(row)
        if key in indexed:
            raise ValueError("Duplicate registry physical identity")
        indexed[key] = row
    return indexed


def _validate_capture_header(capture, registry):
    if capture.get("native_capture_completed") is not True:
        raise ValueError("Native capture is incomplete")
    if capture.get("model_class") != MODEL_CLASS:
        raise ValueError("Native capture is not the frozen M95 model")
    for field in (
        "producer_sha256",
        "config_sha256",
        "model_source_sha256",
        "checkpoint_sha256",
    ):
        _require_hash(capture.get(field), field)
    frozen_producer_sha256 = frozen_capture_producer_sha256()
    if capture["producer_sha256"].lower() != frozen_producer_sha256:
        raise ValueError("Capture producer hash differs from frozen producer bundle")

    config_path = capture.get("config_path")
    if not isinstance(config_path, str) or not config_path:
        raise ValueError("Capture config path is missing")
    if Path(config_path).stem != MODEL_CLASS:
        raise ValueError("Capture config path differs from the frozen model")

    source_config = registry.get("sources", {}).get("config")
    if not isinstance(source_config, dict):
        raise ValueError("Registry source config is missing")
    registry_config_path = source_config.get("path")
    if not isinstance(registry_config_path, str) or Path(registry_config_path).stem != MODEL_CLASS:
        raise ValueError("Registry source config differs from the frozen model")
    if capture["config_sha256"].lower() != _require_hash(
        source_config.get("sha256"), "registry config"
    ):
        raise ValueError("Capture config hash differs from the frozen registry")


def native_capture_binding(capture, registry, code_commit):
    """Derive the evaluator binding from a verified native capture header."""
    _validate_capture_header(capture, registry)
    return {
        "code_commit": _require_hash(code_commit, "code_commit", length=40),
        "config_sha256": capture["config_sha256"].lower(),
        "model_package_sha256": capture["model_source_sha256"].lower(),
        "checkpoint_sha256": capture["checkpoint_sha256"].lower(),
    }


def _validate_query_row(row):
    scores = row.get("scores")
    ious = row.get("ious")
    seed_indices = row.get("sampled_seed_indices")
    labels = row.get("instance_labels")
    support_ids = row.get("original_superpoint_ids")
    if not isinstance(scores, list) or not scores:
        raise ValueError("Native confidence axis is missing")
    if not all(isinstance(item, list) for item in (ious, seed_indices, labels, support_ids)):
        raise ValueError("Native query or support axis is missing")
    if len(scores) != len(ious) or len(scores) != len(seed_indices):
        raise ValueError("Native query axes differ")
    if len(labels) != len(support_ids) or not labels:
        raise ValueError("Native superpoint axes differ")
    objectness = row.get("objectness_scores")
    if row.get("objectness_score_semantics") != OBJECTNESS_SEMANTICS:
        raise ValueError("Target-independent objectness semantics are missing")
    if not isinstance(objectness, list) or len(objectness) != len(scores):
        raise ValueError("Native objectness axis is missing or differs from queries")
    for value in objectness:
        _probability(value, "native objectness")
    fps = row.get("fps_superpoints")
    if not isinstance(fps, list) or not fps:
        raise ValueError("Native FPS axis is missing")
    if any(
        isinstance(item, bool)
        or not isinstance(item, int)
        or not 0 <= item < len(labels)
        for item in fps
    ):
        raise ValueError("Native FPS superpoint index is invalid")
    for index, seed_index in enumerate(seed_indices):
        if (
            isinstance(seed_index, bool)
            or not isinstance(seed_index, int)
            or seed_index < 0
            or seed_index >= len(fps)
        ):
            raise ValueError("Native query seed index is invalid")
        _probability(scores[index], "native confidence")
        _probability(ious[index], "native IoU")
    # sample_inds indexes the entry FPS axis, not the native superpoint axis.
    return scores, objectness, [fps[index] for index in seed_indices], labels


def produce_expression_inputs(capture, registry):
    """Return exact rows accepted by the frozen object-rank capture builder."""
    registry_by_key = _validate_registry(registry)
    _validate_capture_header(capture, registry)

    capture_rows = capture.get("rows")
    if not isinstance(capture_rows, list) or not capture_rows:
        raise ValueError("Native capture rows are missing")
    capture_by_key = {}
    for row in capture_rows:
        key = _physical_key_from_capture(row)
        if key not in registry_by_key:
            raise ValueError("Native capture contains an unregistered expression")
        if key in capture_by_key:
            raise ValueError("Duplicate native capture expression")
        capture_by_key[key] = row

    eligible = [
        (key, row)
        for key, row in registry_by_key.items()
        if row.get("primary_rank_eligible") is True
    ]
    if not eligible:
        raise ValueError("Registry has no rank-eligible expressions")

    output = []
    for key, registry_row in sorted(eligible):
        capture_row = capture_by_key.get(key)
        if capture_row is None:
            raise ValueError("Native capture is missing a rank-eligible expression")
        scores, objectness, seed_indices, labels = _validate_query_row(capture_row)
        output.append({
            "registry_key": registry_row.get("registry_key"),
            "scene": registry_row["scene"],
            "target_object_id": registry_row["target_object_id"],
            "native_input_sha256": _require_hash(
                capture_row.get("native_input_sha256"), "native_input_sha256"
            ),
            "hierarchical_partition_sha256": _require_hash(
                capture_row.get("hierarchical_partition_sha256"),
                "hierarchical_partition_sha256",
            ),
            "instance_labels": labels,
            "query_seed_indices": seed_indices,
            "referent_costs": [
                0.0 if value == 0.0 else -value
                for value in (float(item) for item in scores)
            ],
            "objectness_costs": [
                0.0 if value == 1.0 else 1.0 - value
                for value in (float(item) for item in objectness)
            ],
        })
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    capture_path = Path(args.capture).resolve()
    registry_path = Path(args.registry).resolve()
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    rows = produce_expression_inputs(capture, registry)
    output_path = Path(args.output).resolve()
    output_path.write_text(
        json.dumps(rows, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps({
        "capture_sha256": file_sha256(capture_path),
        "registry_sha256": file_sha256(registry_path),
        "expression_rows": len(rows),
        "output_sha256": file_sha256(output_path),
    }, indent=2))


if __name__ == "__main__":
    main()
