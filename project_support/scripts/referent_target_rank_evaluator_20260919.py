"""Fail-closed evaluation for the frozen outcome-independent referent audit.

The evaluator consumes a predeclared registry and a native capture artifact. It
does not run a model and never imputes a missing query, score, mask, input hash,
or partition hash.
"""
import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


SCORE_NAMES = ("referent", "objectness")
SCORE_DIRECTION = "lower_is_better"
MISSING_DATA_POLICY = "reject_expression_no_imputation"
TIE_POLICY = "reject"
HEX40 = set("0123456789abcdef")
HEX64 = set("0123456789abcdef")


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_sha256(value):
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _is_hex(value, length):
    if not isinstance(value, str) or len(value) != length:
        return False
    alphabet = HEX40 if length == 40 else HEX64
    return all(character in alphabet for character in value.lower())


def validate_registry_document(registry):
    if registry.get("schema_version") != 1:
        raise ValueError("Unsupported registry schema")
    rows = registry.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Registry rows are missing")
    if registry.get("registry_sha256") != stable_sha256(rows):
        raise ValueError("Registry content hash mismatch")

    keys = []
    for row in rows:
        key = row.get("registry_key")
        if not isinstance(key, str) or not key:
            raise ValueError("Registry key is missing")
        keys.append(key)
        candidates = row.get("same_class_candidate_ids")
        if not isinstance(candidates, list):
            raise ValueError("Candidate pool is missing")
        if candidates != sorted(set(candidates)):
            raise ValueError("Candidate pool must be sorted and unique")
        if row.get("target_object_id") in candidates:
            raise ValueError("Target cannot be its own candidate")
        if row.get("primary_rank_eligible") != bool(candidates):
            raise ValueError("Rank eligibility differs from candidate pool")
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate registry key")
    return rows


def validate_capture_document(capture, registry):
    if capture.get("schema_version") != 1:
        raise ValueError("Unsupported capture schema")
    if capture.get("registry_sha256") != registry.get("registry_sha256"):
        raise ValueError("Capture is bound to a different registry")

    contract = capture.get("capture_contract")
    expected = {
        "score_direction": SCORE_DIRECTION,
        "missing_data_policy": MISSING_DATA_POLICY,
        "required_score_names": list(SCORE_NAMES),
        "tie_policy": TIE_POLICY,
    }
    if contract != expected:
        raise ValueError("Capture contract differs from the frozen evaluator")

    binding = capture.get("binding")
    if not isinstance(binding, dict):
        raise ValueError("Capture binding is missing")
    if not _is_hex(binding.get("code_commit"), 40):
        raise ValueError("Capture code commit is invalid")
    for field in ("config_sha256", "model_package_sha256", "checkpoint_sha256"):
        if not _is_hex(binding.get(field), 64):
            raise ValueError("Capture binding hash is invalid: " + field)

    rows = capture.get("rows")
    if not isinstance(rows, list):
        raise ValueError("Capture rows are missing")
    by_key = {}
    for row in rows:
        key = row.get("registry_key")
        if key in by_key:
            raise ValueError("Duplicate capture registry key")
        by_key[key] = row
    return by_key


def _validate_score_map(row, score_name, expected_ids):
    scores = row.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(SCORE_NAMES):
        raise ValueError("Required score axes are missing")
    score_map = scores.get(score_name)
    if not isinstance(score_map, dict) or set(score_map) != set(expected_ids):
        raise ValueError("Native candidate coverage differs from registry")

    values = []
    for object_id in expected_ids:
        value = score_map[object_id]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Native score is not numeric")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("Native score is nonfinite")
        values.append(value)
    if len(values) != len(set(values)):
        raise ValueError("Native score ties are not admissible")
    return score_map


def rank_capture_row(capture_row, registry_row):
    if capture_row.get("scene") != registry_row.get("scene"):
        raise ValueError("Capture scene differs from registry")
    if capture_row.get("target_object_id") != registry_row.get("target_object_id"):
        raise ValueError("Capture target differs from registry")

    for field in ("native_input_sha256", "hierarchical_partition_sha256"):
        if not _is_hex(capture_row.get(field), 64):
            raise ValueError("Capture identity hash is invalid: " + field)

    expected_ids = [
        registry_row["target_object_id"],
        *registry_row["same_class_candidate_ids"],
    ]
    mask_hashes = capture_row.get("mask_sha256")
    if not isinstance(mask_hashes, dict) or set(mask_hashes) != set(expected_ids):
        raise ValueError("Native mask coverage differs from registry")
    if any(not _is_hex(mask_hashes[object_id], 64) for object_id in expected_ids):
        raise ValueError("Native mask identity hash is invalid")

    result = {}
    for score_name in SCORE_NAMES:
        score_map = _validate_score_map(capture_row, score_name, expected_ids)
        ordered = sorted(expected_ids, key=lambda object_id: score_map[object_id])
        target_id = registry_row["target_object_id"]
        rank = ordered.index(target_id) + 1
        result[score_name] = {
            "rank": rank,
            "pool_size": len(ordered),
            "top1": rank == 1,
            "normalized_excess": (
                0.0 if len(ordered) == 1 else (rank - 1) / (len(ordered) - 1)
            ),
        }
    return result


def _percentile(values, probability):
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Cannot compute percentile of an empty sample")
    position = probability * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _scene_balanced(rows, score_name, field):
    by_scene = defaultdict(list)
    for row in rows:
        by_scene[row["scene"]].append(row["scores"][score_name][field])
    scene_means = [
        sum(values) / len(values) for values in by_scene.values()
    ]
    return sum(scene_means) / len(scene_means)


def _scene_bootstrap(rows, score_name, field, draws=2000):
    by_scene = defaultdict(list)
    for row in rows:
        by_scene[row["scene"]].append(row["scores"][score_name][field])
    scenes = list(by_scene.values())
    seed_material = (
        str(rows[0]["registry_key"]) + ":" + score_name + ":" + field
    ).encode("ascii")
    seed = int(hashlib.sha256(seed_material).hexdigest()[:16], 16)
    rng = random.Random(seed)
    draws_out = []
    for _ in range(draws):
        sampled = [scenes[rng.randrange(len(scenes))] for _ in scenes]
        scene_means = [
            sum(values) / len(values) for values in sampled
        ]
        draws_out.append(sum(scene_means) / len(scene_means))
    return {
        "low": _percentile(draws_out, 0.025),
        "high": _percentile(draws_out, 0.975),
        "draws": draws,
    }


def _score_summary(rows, score_name):
    top1 = _scene_balanced(rows, score_name, "top1")
    normalized_excess = _scene_balanced(
        rows, score_name, "normalized_excess"
    )
    uniform_top1 = _scene_balanced(
        [
            {
                **row,
                "scores": {
                    **row["scores"],
                    score_name: {
                        **row["scores"][score_name],
                        "top1": 1.0 / row["scores"][score_name]["pool_size"],
                        "normalized_excess": 0.5,
                    },
                },
            }
            for row in rows
        ],
        score_name,
        "top1",
    )
    return {
        "scene_balanced_top1_success": top1,
        "scene_balanced_top1_ci95": _scene_bootstrap(rows, score_name, "top1"),
        "uniform_scene_balanced_top1_success": uniform_top1,
        "top1_lift_over_uniform": top1 - uniform_top1,
        "scene_balanced_normalized_rank_excess": normalized_excess,
        "normalized_rank_excess_ci95": _scene_bootstrap(
            rows, score_name, "normalized_excess"
        ),
        "uniform_scene_balanced_normalized_rank_excess": 0.5,
        "expression_top1_success": sum(
            bool(row["scores"][score_name]["top1"]) for row in rows
        ) / len(rows),
        "expression_mean_rank": sum(
            row["scores"][score_name]["rank"] for row in rows
        ) / len(rows),
    }


def evaluate_capture(registry, capture):
    registry_rows = validate_registry_document(registry)
    capture_rows = validate_capture_document(capture, registry)
    eligible = [
        row for row in registry_rows if row["primary_rank_eligible"]
    ]
    valid = []
    rejected = []
    for registry_row in eligible:
        key = registry_row["registry_key"]
        capture_row = capture_rows.get(key)
        if capture_row is None:
            rejected.append({"registry_key": key, "reason": "missing_expression"})
            continue
        try:
            scores = rank_capture_row(capture_row, registry_row)
        except ValueError as exc:
            rejected.append({"registry_key": key, "reason": str(exc)})
            continue
        valid.append({
            "registry_key": key,
            "scene": registry_row["scene"],
            "target_object_id": registry_row["target_object_id"],
            "scores": scores,
        })

    if not valid:
        raise ValueError("No expression passed the complete-coverage contract")

    return {
        "registry_expressions": len(registry_rows),
        "registry_rank_eligible_expressions": len(eligible),
        "complete_rank_eligible_expressions": len(valid),
        "rejected_rank_eligible_expressions": len(rejected),
        "valid_scenes": len({row["scene"] for row in valid}),
        "rejected": rejected,
        "score_summaries": {
            score_name: _score_summary(valid, score_name)
            for score_name in SCORE_NAMES
        },
        "rows": valid,
    }


def build_report(registry, capture, registry_path, capture_path):
    summary = evaluate_capture(registry, capture)
    return {
        "schema_version": 1,
        "scope": (
            "CPU-only fail-closed evaluation contract for the frozen "
            "outcome-independent referent target-rank audit; no model forward, "
            "native score, GPU execution, or efficacy claim"
        ),
        "inputs": {
            "registry": {
                "path": str(registry_path),
                "sha256": file_sha256(registry_path),
                "content_sha256": registry["registry_sha256"],
            },
            "capture": {
                "path": str(capture_path),
                "sha256": file_sha256(capture_path),
            },
        },
        "binding": capture["binding"],
        "evaluation_contract": {
            "score_direction": SCORE_DIRECTION,
            "missing_data_policy": MISSING_DATA_POLICY,
            "tie_policy": TIE_POLICY,
            "scene_balance": (
                "equal scene means over expressions that pass complete native "
                "coverage; missing expressions are rejected, never imputed"
            ),
            "controls": list(SCORE_NAMES),
        },
        "summary": summary,
        "limitations": [
            "This is a fixed TRAIN diagnostic, not held-out population evidence.",
            "Score direction must match the predeclared native score contract.",
            "Missing candidate, score, mask, input, or partition evidence "
            "invalidates that expression.",
            "Exact native identity does not certify identical model-internal "
            "random draws.",
            "Hash and coverage validity do not establish scientific validity.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True)
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    registry_path = Path(args.registry).resolve()
    capture_path = Path(args.capture).resolve()
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    report = build_report(
        registry,
        capture,
        registry_path=registry_path,
        capture_path=capture_path,
    )
    Path(args.output).write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
