"""Failure-local geometry denominators with an explicit physical join manifest.

Registry metadata lacks native input identity. Never infer a native join from
scene/annotation alone; callers must supply and externally verify full bindings.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path

from frozen_capture_contract_20260916 import file_sha256, fingerprint
from referent_geometry_capture_20260919 import (
    check_binding, identity, require_hash, validate_capture,
)
from referent_geometry_control_20260919 import geometry_control


CONTRACT = "failure_local_geometry_registry_v1"
STATES = ("missing_binding", "missing_capture", "missing_geometry", "tied", "valid")


def canonical_id(value):
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        if str(int(value)) == value:
            return int(value)
    raise ValueError("Canonical nonnegative physical ID required")


def registry_pairs(registry):
    pairs, seen = [], set()
    for item in registry["pairs"]:
        scene, slot = item["scene"], canonical_id(item["expression_slot"])
        ann = canonical_id(item["ann_id"])
        expected = "%s:%s:%s" % (scene, slot, ann)
        if not isinstance(scene, str) or not scene or item["pair_id"] != expected:
            raise ValueError("Noncanonical registry pair")
        if expected in seen:
            raise ValueError("Duplicate registry pair")
        seen.add(expected)
        target = canonical_id(item["target_object_id"])
        control = canonical_id(item["observed_control_object_id"])
        if target == control:
            raise ValueError("Self contrast")
        eligible = item["primary_same_class_pair_eligible"]
        if type(eligible) is not bool:
            raise ValueError("Boolean eligibility required")
        if eligible:
            pool = [canonical_id(x) for x in item["same_class_control_pool"]]
            if control not in pool:
                raise ValueError("Control outside same-class pool")
            pairs.append(item)
    return pairs


def contrast(costs, ids):
    values = [costs.get(str(obj)) for obj in ids]
    if any(value is None for value in values):
        return dict(status="missing_geometry", values=values, near_tie=False,
                    target_lower_cost=None)
    a, b = values
    return dict(status="tied" if a == b else "valid", values=values,
                near_tie=math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12),
                target_lower_cost=None if a == b else a < b)


def denominator(rows):
    counts = Counter(row["status"] for row in rows)
    return dict(
        requested=len(rows), counts={state: counts[state] for state in STATES},
        near_ties=sum(row.get("near_tie", False) for row in rows),
        target_lower_cost=sum(row.get("target_lower_cost") is True for row in rows),
        non_near_tied_valid=sum(row["status"] == "valid" and not row["near_tie"]
                               for row in rows),
    )


def evaluate(registry, registry_sha256, captures, source_binding, joins):
    """Evaluate geometry sidecars; this function cannot attest native execution."""
    require_hash(registry_sha256)
    if source_binding is None:
        if captures:
            raise ValueError("Captured data requires source binding")
    else:
        check_binding(source_binding)
    pairs = registry_pairs(registry)
    if joins.get("registry_sha256") != registry_sha256:
        raise ValueError("Join registry hash mismatch")
    eligible = {p["pair_id"]: p for p in pairs}
    joined, used = {}, set()
    for join in joins["bindings"]:
        pair_id = join["pair_id"]
        if pair_id not in eligible or pair_id in joined:
            raise ValueError("Unknown or duplicate joined pair")
        physical = identity(join["identity"])
        if set(join["identity"]) != set(physical):
            raise ValueError("Exact physical join identity required")
        pair = eligible[pair_id]
        if (physical["scene"] != pair["scene"]
                or physical["expression_slot"] != canonical_id(pair["expression_slot"])
                or physical["ann_id"] != canonical_id(pair["ann_id"])):
            raise ValueError("Registry/native join mismatch")
        key = fingerprint(physical)
        if key in used:
            raise ValueError("Native expression reused for multiple registry pairs")
        used.add(key)
        joined[pair_id] = key
    native = {}
    for capture in captures:
        if "runtime_contract" in capture:
            if (capture["runtime_contract"] != "criterion_geometry_runtime_v1"
                    or capture.get("criterion_calls") != 1
                    or type(capture.get("loss")) not in (int, float)
                    or not math.isfinite(capture["loss"])):
                raise ValueError("Invalid runtime sidecar")
            payload = {k: v for k, v in capture.items() if k != "payload_sha256"}
            if fingerprint(payload) != capture.get("payload_sha256"):
                raise ValueError("Runtime sidecar hash mismatch")
            require_hash(capture["collated_input_sha256"])
            capture = capture["geometry"]
        for row in validate_capture(capture, source_binding):
            key = fingerprint(row["identity"])
            if key in native:
                raise ValueError("Duplicate native expression across sidecars")
            native[key] = row
    results = []
    for pair in pairs:
        row = dict(pair_id=pair["pair_id"], scene=pair["scene"],
                   status="missing_binding")
        key = joined.get(pair["pair_id"])
        if key is not None:
            row["status"] = "missing_capture"
        if key in native:
            observed = native[key]
            ids = [canonical_id(pair[field]) for field in
                   ("target_object_id", "observed_control_object_id")]
            row.update(contrast(observed["geometry"]["object_costs"], ids))
            # Keep support fixed and remove only language-selected subsampling.
            fps = geometry_control(observed["coordinates"],
                                   observed["physical_instance_labels"],
                                   observed["fps_superpoints"])
            alternate = contrast(fps["object_costs"], ids)
            row["fps_reference"] = alternate
            row["selected_query_count"] = len(observed["composed_seed_indices"])
            row["fps_query_count"] = len(observed["fps_superpoints"])
            row["selection_cost_changed"] = row["values"] != alternate["values"]
            row["selection_status_changed"] = row["status"] != alternate["status"]
            row["selection_order_changed"] = (
                row["status"] == alternate["status"] == "valid"
                and row["target_lower_cost"] != alternate["target_lower_cost"])
        results.append(row)
    scenes = sorted({row["scene"] for row in results})
    per_scene = {scene: denominator([r for r in results if r["scene"] == scene])
                 for scene in scenes}
    observed = [row for row in results if "fps_reference" in row]
    return dict(
        contract=CONTRACT, registry_sha256=registry_sha256,
        join_sha256=fingerprint(joins), source_binding=source_binding,
        overall=denominator(results), per_scene=per_scene, pairs=results,
        scene_balanced_status_fractions={
            state: (sum(d["counts"][state] / d["requested"] for d in per_scene.values())
                    / len(scenes) if scenes else None)
            for state in STATES
        },
        selection_sensitivity=dict(
            captured_pairs=len(observed),
            cost_changed=sum(r["selection_cost_changed"] for r in observed),
            status_changed=sum(r["selection_status_changed"] for r in observed),
            order_changed=sum(r["selection_order_changed"] for r in observed),
            fps_denominators=denominator([r["fps_reference"] for r in observed])),
        unmatched_sidecar_rows=len(set(native) - set(joined.values())),
        native_execution_verified=False, scientific_validation_complete=False,
        population_effect_admissible=False, independent_objectness_resolved=False,
        limitations=[
            "Failure-selected target/control registry, not a population sample.",
            "Join bindings require external native-dataset verification; hashes do not prove it.",
            "Annotation-assisted radial geometry is not objectness or efficacy.",
            "FPS versus selected queries diagnoses selection sensitivity, not independence.",
            "Scene-balanced denominators retain every eligible pair, including missing pairs.",
        ],
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True)
    parser.add_argument("--joins", required=True)
    parser.add_argument("--binding", required=True)
    parser.add_argument("--captures", nargs="*", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    def read(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))
    report = evaluate(read(args.registry), file_sha256(args.registry),
                      [read(path) for path in args.captures],
                      read(args.binding), read(args.joins))
    with Path(args.output).open("x", encoding="ascii") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
