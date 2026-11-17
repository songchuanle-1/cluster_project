"""Separate geometry nuisance contract; never emits objectness scores.

This adapter consumes observed criterion arguments. It does not install hooks,
launch native inference, or authorize mechanism admission.
"""
import copy
import math

from capture_support_20260916 import support_record
from frozen_capture_contract_20260916 import fingerprint
from referent_geometry_control_20260919 import geometry_control, SEMANTICS


CONTRACT = "criterion_geometry_nuisance_v2"
BINDING_FIELDS = ("producer_sha256", "model_source_sha256",
                  "config_sha256", "checkpoint_sha256")
IDENTITY_FIELDS = ("capture_id", "scene", "scene_occurrence", "dataset_index",
                   "ann_id", "expression_slot", "native_input_sha256",
                   "original_superpoint_ids", "sample_inverse")


def plain(value):
    if hasattr(value, "detach"):
        value = value.detach().cpu()
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


def require_hash(value):
    if (not isinstance(value, str) or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)):
        raise ValueError("Canonical SHA256 required")


def check_binding(binding):
    if not isinstance(binding, dict) or set(binding) != set(BINDING_FIELDS):
        raise ValueError("Exact source binding required")
    for value in binding.values():
        require_hash(value)


def integer_axis(values, limit=None):
    if not isinstance(values, list) or not values:
        raise ValueError("Nonempty integer axis required")
    if any(type(x) is not int or x < 0 or (limit is not None and x >= limit)
           for x in values):
        raise ValueError("Invalid integer axis")


def native_labels(values):
    """Native dataset labels are float tensors; reject lossy integer conversion."""
    if not isinstance(values, list) or not values:
        raise ValueError("Nonempty native instance labels required")
    result = []
    for value in values:
        if (type(value) not in (int, float) or not math.isfinite(value)
                or abs(value) > 2 ** 53 or int(value) != value):
            raise ValueError("Native instance labels must be exactly integral")
        result.append(int(value))
    return result


def identity(axis):
    result = {key: copy.deepcopy(axis[key]) for key in IDENTITY_FIELDS}
    for key in ("capture_id", "scene"):
        if not isinstance(result[key], str) or not result[key]:
            raise ValueError("Missing physical identity")
    for key in ("scene_occurrence", "dataset_index", "ann_id", "expression_slot"):
        if type(result[key]) is not int or result[key] < 0:
            raise ValueError("Noncanonical physical identity")
    require_hash(result["native_input_sha256"])
    support_record(result["original_superpoint_ids"], result["sample_inverse"])
    return result


def capture_batch(inputs, axes, binding):
    """Read input4 labels, input7 FPS, input8 coordinates, input9 offsets."""
    check_binding(binding)
    if len(inputs) != 10 or not isinstance(axes, list) or not axes:
        raise ValueError("Exact criterion signature and expression axes required")
    labels, fps, coordinates, offsets, samples = [
        plain(value) for value in
        (inputs[4], inputs[7], inputs[8], inputs[9], inputs[0]["sample_inds"])
    ]
    integer_axis(offsets)
    if (len(offsets) != len(axes) + 1 or offsets[0] != 0
            or offsets[-1] != len(coordinates)
            or any(a >= b for a, b in zip(offsets, offsets[1:]))):
        raise ValueError("Invalid expression offsets")
    if any(len(value) != len(axes) for value in (labels, fps, samples)):
        raise ValueError("Expression axis mismatch")
    observed_hash = fingerprint(
        [inputs[4], inputs[7], inputs[8], inputs[9], inputs[0]["sample_inds"]])
    rows, keys = [], set()
    for b, axis in enumerate(axes):
        physical = identity(axis)
        key = tuple(physical[k] for k in IDENTITY_FIELDS[:6])
        if key in keys:
            raise ValueError("Duplicate physical expression")
        keys.add(key)
        start, end = offsets[b:b + 2]
        n = end - start
        if len(physical["original_superpoint_ids"]) != n or len(labels[b]) != n:
            raise ValueError("Coordinate support differs from physical labels")
        if axis.get("producer_sha256") != binding["producer_sha256"]:
            raise ValueError("Producer binding mismatch")
        if axis.get("checkpoint_sha256") != binding["checkpoint_sha256"]:
            raise ValueError("Checkpoint binding mismatch")
        actual_labels = plain(axis["physical_instance_labels"])
        normalized_labels = native_labels(labels[b])
        if len(actual_labels) != n:
            raise ValueError("Instance label axis mismatch")
        # Native majority voting uses 199 for unresolved support. The physical
        # binding disambiguates that sentinel from a real instance with ID199.
        for native, actual in zip(normalized_labels, actual_labels):
            if type(actual) is not int:
                raise ValueError("Integer physical labels required")
            if actual != native and not (actual == -1 and native == 199):
                raise ValueError("Physical/native instance binding mismatch")
        integer_axis(fps[b], n)
        integer_axis(samples[b], len(fps[b]))
        seeds = [fps[b][index] for index in samples[b]]
        coords = coordinates[start:end]
        result = geometry_control(coords, actual_labels, seeds)
        row = dict(identity=physical, coordinates=coords,
                   native_instance_labels=normalized_labels,
                   observed_native_instance_labels=labels[b],
                   physical_instance_labels=actual_labels,
                   fps_superpoints=fps[b], sampled_seed_indices=samples[b],
                   composed_seed_indices=seeds, geometry=result)
        rows.append(row)
    payload = dict(contract=CONTRACT, binding=copy.deepcopy(binding),
                   observed_criterion_sha256=observed_hash, offsets=offsets,
                   rows=rows, semantics=SEMANTICS)
    payload = copy.deepcopy(payload)
    payload["payload_sha256"] = fingerprint(payload)
    return payload


def validate_capture(capture, expected_binding):
    check_binding(expected_binding)
    if capture.get("contract") != CONTRACT or capture.get("semantics") != SEMANTICS:
        raise ValueError("Wrong geometry contract")
    if capture.get("binding") != expected_binding:
        raise ValueError("Source binding differs")
    payload = {k: v for k, v in capture.items() if k != "payload_sha256"}
    if fingerprint(payload) != capture.get("payload_sha256"):
        raise ValueError("Geometry payload hash mismatch")
    require_hash(capture["observed_criterion_sha256"])
    rows = capture["rows"]
    if not rows:
        raise ValueError("Missing geometry rows")
    # Re-run all structural checks and costs, including physical ID199 handling.
    axes = [dict(row["identity"], physical_instance_labels=row["physical_instance_labels"],
                 producer_sha256=expected_binding["producer_sha256"],
                 checkpoint_sha256=expected_binding["checkpoint_sha256"]) for row in rows]
    inputs = [None] * 10
    inputs[0] = {"sample_inds": [r["sampled_seed_indices"] for r in rows]}
    inputs[4] = [r["observed_native_instance_labels"] for r in rows]
    inputs[7] = [r["fps_superpoints"] for r in rows]
    inputs[8] = [point for r in rows for point in r["coordinates"]]
    inputs[9] = capture["offsets"]
    rebuilt = capture_batch(inputs, axes, expected_binding)
    if rebuilt["rows"] != rows:
        raise ValueError("Geometry recomputation mismatch")
    return rows


def evaluate_contrasts(capture, expected_binding, contrasts):
    """Report missing/tied denominators; no efficacy or population inference."""
    rows = validate_capture(capture, expected_binding)
    results = []
    for item in contrasts:
        if set(item) != {"row_index", "object_ids"}:
            raise ValueError("Exact contrast definition required")
        index, ids = item["row_index"], item["object_ids"]
        if type(index) is not int or not 0 <= index < len(rows):
            raise ValueError("Contrast row outside capture")
        integer_axis(ids)
        if len(ids) < 2 or len(set(ids)) != len(ids):
            raise ValueError("Distinct contrast objects required")
        costs = rows[index]["geometry"]["object_costs"]
        missing = [obj for obj in ids if str(obj) not in costs]
        values = [costs[str(obj)] for obj in ids if str(obj) in costs]
        gaps = [abs(a - b) for i, a in enumerate(values) for b in values[i + 1:]]
        status = ("missing" if missing else "tied" if len(set(values)) < len(ids)
                  else "valid")
        results.append(dict(row_index=index, object_ids=ids, status=status,
                            missing_object_ids=missing, values=values,
                            minimum_absolute_gap=min(gaps) if gaps else None,
                            near_tie=any(math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)
                                         for i, a in enumerate(values)
                                         for b in values[i + 1:])))
    return dict(contract=CONTRACT, requested_contrasts=len(results),
                counts={state: sum(r["status"] == state for r in results)
                        for state in ("valid", "missing", "tied")},
                contrasts=results, native_execution_verified=False,
                scientific_validation_complete=False)
