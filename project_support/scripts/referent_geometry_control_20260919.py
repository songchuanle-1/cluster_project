"""Target-blind geometry nuisance control, not objectness or a learned score.

Inputs are the exact transformed superpoint coordinates, all instance labels
and composed native seed indices. No target, text, mask prediction or score is
accepted. Labels make this an annotation-assisted diagnostic, not deployment.
"""
import math


SEMANTICS = "annotation_assisted_seed_radial_cost_not_objectness_v1"


def geometry_control(coordinates, instance_labels, query_seed_indices):
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError("Nonempty coordinate axis required")
    if not isinstance(instance_labels, list) or len(instance_labels) != len(coordinates):
        raise ValueError("Instance-label axis differs from coordinates")
    if any(type(label) is not int for label in instance_labels):
        raise ValueError("Integer instance labels required")
    for point in coordinates:
        if not isinstance(point, list) or len(point) != 3:
            raise ValueError("Three-dimensional coordinates required")
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in point):
            raise ValueError("Finite numeric coordinates required")
    if not isinstance(query_seed_indices, list) or not query_seed_indices:
        raise ValueError("Nonempty composed seed axis required")
    if any(type(seed) is not int or not 0 <= seed < len(coordinates)
           for seed in query_seed_indices):
        raise ValueError("Composed seed outside coordinate support")

    members = {}
    for index, label in enumerate(instance_labels):
        if label >= 0:
            members.setdefault(label, []).append(index)
    if not members:
        raise ValueError("No annotated instances")

    # Normalize radial distance by each object's own mean squared radius.
    # This removes global translation/rotation/scale without a tunable constant.
    support_costs = [None] * len(coordinates)
    degenerate = []
    for label, indices in members.items():
        center = [math.fsum(coordinates[i][d] / len(indices) for i in indices)
                  for d in range(3)]
        distances = [
            math.fsum((coordinates[i][d] - center[d]) ** 2 for d in range(3))
            for i in indices
        ]
        radius = math.fsum(distance / len(indices) for distance in distances)
        if not math.isfinite(radius):
            raise ValueError("Nonfinite geometric scale")
        if radius == 0:
            degenerate.append(label)
            continue
        for index, distance in zip(indices, distances):
            support_costs[index] = distance / radius

    query_costs = [support_costs[seed] for seed in query_seed_indices]
    object_costs = {}
    for label in members:
        values = [query_costs[q] for q, seed in enumerate(query_seed_indices)
                  if instance_labels[seed] == label]
        if values and all(value is not None for value in values):
            object_costs[str(label)] = min(values)
    return {
        "semantics": SEMANTICS,
        "support_costs": support_costs,
        "query_costs": query_costs,
        "object_costs": object_costs,
        "degenerate_object_ids": sorted(degenerate),
        "target_independence": "conditional_on_fixed_support_labels_and_seed_axis",
    }


def validate_contrast(result, object_ids):
    """Reject missing support and exact ties; never turn them into successes."""
    if result.get("semantics") != SEMANTICS:
        raise ValueError("Not the geometry nuisance contract")
    if (not isinstance(object_ids, list) or len(object_ids) < 2
            or any(type(x) is not int or x < 0 for x in object_ids)
            or len(set(object_ids)) != len(object_ids)):
        raise ValueError("At least two distinct physical objects required")
    values = []
    for object_id in object_ids:
        value = result["object_costs"].get(str(object_id))
        if value is None:
            raise ValueError("Missing coverage or degenerate geometry")
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid geometry cost")
        values.append(value)
    if len(set(values)) != len(values):
        raise ValueError("Tied geometry contrast")
    return values
