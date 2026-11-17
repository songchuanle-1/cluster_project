"""Serialize and validate exogenous hierarchical FPS partition geometry."""
import hashlib
import json
import math


def _integer(value, label):
    if type(value) is not int:
        raise ValueError("Invalid integer for " + label)
    return value


def _child_map_parent(value):
    if type(value) is int:
        return value
    if (
        isinstance(value, str)
        and value.isascii()
        and value.isdigit()
        and (value == "0" or not value.startswith("0"))
    ):
        return int(value)
    raise ValueError("Invalid child-map parent")


def _finite(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Invalid number for " + label)
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Nonfinite number for " + label)
    return value


def _canonical_child_mapping(mapping):
    if not isinstance(mapping, dict):
        raise ValueError("Invalid hierarchical child map")
    normalized = {}
    for parent, children in mapping.items():
        parent = _child_map_parent(parent)
        if parent < 0 or parent in normalized:
            raise ValueError("Invalid child-map parent")
        if not isinstance(children, list) or not children:
            raise ValueError("Invalid child-map children")
        values = []
        seen = set()
        for child in children:
            child = _integer(child, "child-map child")
            if child < 0 or child in seen:
                raise ValueError("Invalid or duplicate child-map child")
            seen.add(child)
            values.append(child)
        normalized[parent] = values
    return {str(key): normalized[key] for key in sorted(normalized)}


def hierarchical_partition_sha256(fps_positions, cluster_ids, child_maps):
    payload = dict(
        fps_positions=fps_positions,
        cluster_ids=cluster_ids,
        child_maps=child_maps)
    raw = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("ascii")).hexdigest()


def validate_hierarchical_partition(n0, fps_positions, cluster_ids, child_maps):
    """Validate one expression and return its canonical partition hash."""
    n0 = _integer(n0, "level-0 support size")
    if n0 < 1:
        raise ValueError("Level-0 support must be nonempty")
    if not isinstance(fps_positions, list) or not fps_positions:
        raise ValueError("Missing hierarchical FPS positions")
    if len(cluster_ids) != len(fps_positions):
        raise ValueError("Hierarchical level count differs")
    if len(child_maps) != len(fps_positions) - 1:
        raise ValueError("Hierarchical child-map count differs")

    canonical_positions = []
    canonical_ids = []
    expected_size = n0
    for level, centers in enumerate(fps_positions):
        if not isinstance(centers, list) or not centers:
            raise ValueError("Hierarchical FPS level is empty")
        level_centers = []
        dimension = None
        for center in centers:
            if not isinstance(center, list) or not center:
                raise ValueError("Invalid hierarchical FPS position")
            if dimension is None:
                dimension = len(center)
            elif len(center) != dimension:
                raise ValueError("Hierarchical FPS position dimensions differ")
            level_centers.append([
                _finite(value, "hierarchical FPS coordinate") for value in center])
        canonical_positions.append(level_centers)

        ids = cluster_ids[level]
        if not isinstance(ids, list) or len(ids) != expected_size:
            raise ValueError("Hierarchical cluster support size differs")
        level_ids = []
        for cluster_id in ids:
            cluster_id = _integer(cluster_id, "hierarchical cluster id")
            if not 0 <= cluster_id < len(level_centers):
                raise ValueError("Hierarchical cluster id out of range")
            level_ids.append(cluster_id)
        canonical_ids.append(level_ids)
        expected_size = len(level_centers)

    canonical_maps = []
    for level, mapping in enumerate(child_maps):
        canonical_maps.append(_canonical_child_mapping(mapping))
        children = []
        for values in canonical_maps[-1].values():
            children.extend(values)
        expected_children = len(fps_positions[level + 1])
        if sorted(children) != list(range(expected_children)):
            raise ValueError("Hierarchical child map is not a partition")
        parent_count = len(fps_positions[level])
        if any(child < 0 or child >= parent_count for child in children):
            raise ValueError("Hierarchical child-map parent out of range")

    return hierarchical_partition_sha256(
        canonical_positions, canonical_ids, canonical_maps)


def partition_rows_from_observations(
        fps_positions, cluster_ids, child_maps, support_sizes, num_levels):
    """Bind flat cluster-layer observations back to expression rows."""
    batch_count = len(support_sizes)
    num_levels = _integer(num_levels, "hierarchical level count")
    if batch_count < 1 or num_levels < 1:
        raise ValueError("Positive batch and level counts required")
    if len(fps_positions) != batch_count * num_levels:
        raise ValueError("Unexpected hierarchical FPS call count")
    if len(cluster_ids) != num_levels:
        raise ValueError("Unexpected hierarchical cluster level count")
    if len(child_maps) != max(num_levels - 1, 0):
        raise ValueError("Unexpected hierarchical child-map level count")
    for level in range(num_levels):
        if len(cluster_ids[level]) != batch_count:
            raise ValueError("Unexpected hierarchical cluster batch count")
    for level in range(num_levels - 1):
        if len(child_maps[level]) != batch_count:
            raise ValueError("Unexpected hierarchical child-map batch count")

    rows = []
    for batch in range(batch_count):
        offset = batch * num_levels
        expression_positions = fps_positions[offset:offset + num_levels]
        expression_ids = [cluster_ids[level][batch]
                          for level in range(num_levels)]
        expression_maps = [child_maps[level][batch]
                           for level in range(num_levels - 1)]
        digest = validate_hierarchical_partition(
            support_sizes[batch], expression_positions,
            expression_ids, expression_maps)
        rows.append(dict(
            hierarchical_fps_positions=expression_positions,
            hierarchical_cluster_ids=expression_ids,
            hierarchical_child_maps=expression_maps,
            hierarchical_partition_sha256=digest))
    return rows


def validate_hierarchical_row(row):
    """Validate row fields and return the canonical partition hash."""
    if not isinstance(row, dict):
        raise ValueError("Hierarchical row must be a dictionary")
    try:
        n0 = len(row["original_superpoint_ids"])
    except (KeyError, TypeError) as exc:
        raise ValueError("Missing original superpoint support") from exc
    try:
        digest = validate_hierarchical_partition(
            n0,
            row["hierarchical_fps_positions"],
            row["hierarchical_cluster_ids"],
            row["hierarchical_child_maps"])
    except KeyError as exc:
        raise ValueError("Missing hierarchical partition fields") from exc
    if row.get("hierarchical_partition_sha256") != digest:
        raise ValueError("Hierarchical partition hash differs")
    entry_fps = row.get("fps_superpoints")
    if entry_fps is not None:
        if not isinstance(entry_fps, list) or not entry_fps:
            raise ValueError("Missing or invalid entry FPS support")
        if any(type(index) is not int or not 0 <= index < n0
               for index in entry_fps):
            raise ValueError("Invalid entry FPS support")
        if len(set(entry_fps)) != len(entry_fps):
            raise ValueError("Duplicate entry FPS support")
    return digest
