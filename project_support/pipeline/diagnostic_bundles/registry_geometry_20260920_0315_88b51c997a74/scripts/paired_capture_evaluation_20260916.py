"""Fail-closed paired diagnostic evaluation; no training or admission effects."""
from collections import defaultdict
import math
import random

from capture_support_20260916 import support_record


def control_manifest(controls):
    grouped = defaultdict(list)
    seen = set()
    for row in controls:
        key = (row["scene"], int(row["ann_id"]), int(row["node_id"]))
        if key in seen:
            raise ValueError("Duplicate control node")
        seen.add(key)
        grouped[key[:2]].append(key[2])
    return [dict(scene=scene, ann_id=ann, node_ids=sorted(nodes))
            for (scene, ann), nodes in sorted(grouped.items())]


def index_rows(rows):
    result = {}
    for row in rows:
        support_record(row["original_superpoint_ids"], row["sample_inverse"])
        if not row["capture_id"] or len(row["producer_sha256"]) != 64:
            raise ValueError("Missing capture provenance")
        int(row["producer_sha256"], 16)
        key = (row["scene"], row["ann_id"], row["scene_occurrence"],
               row["dataset_index"], row["expression_slot"])
        if key in result:
            raise ValueError("Duplicate expression observation")
        scores, ious = row["scores"], row["ious"]
        if not scores or len(scores) != len(ious):
            raise ValueError("Invalid query axes")
        if any(not math.isfinite(x) for x in scores + ious):
            raise ValueError("Nonfinite query evidence")
        if any(not 0 <= x <= 1 for x in ious):
            raise ValueError("Invalid IoU")
        selected = max(range(len(scores)), key=lambda i: (scores[i], -i))
        if selected != row["selected_query"]:
            raise ValueError("Selected query differs from native rule")
        result[key] = row
    if not result:
        raise ValueError("Empty capture")
    return result


def paired_summary(left_rows, right_rows, *, draws=2000):
    left, right = index_rows(left_rows), index_rows(right_rows)
    if left.keys() != right.keys():
        raise ValueError("Paired expression manifest differs")
    if draws < 1:
        raise ValueError("Positive bootstrap draws required")
    scenes = defaultdict(list)
    for key, lhs in left.items():
        rhs = right[key]
        for field in ("original_superpoint_ids", "sample_inverse",
                      "instance_labels", "target_instances"):
            if lhs[field] != rhs[field]:
                raise ValueError("Physical support or target mismatch: " + field)
        a = int(lhs["ious"][lhs["selected_query"]] > .5)
        b = int(rhs["ious"][rhs["selected_query"]] > .5)
        scenes[key[0]].append((a, b))
    rates = {
        scene: dict(expressions=len(values),
                    baseline=sum(a for a, _ in values) / len(values),
                    candidate=sum(b for _, b in values) / len(values))
        for scene, values in sorted(scenes.items())}
    deltas = [v["candidate"] - v["baseline"] for v in rates.values()]
    rng = random.Random(1999)
    bootstrap = sorted(sum(rng.choices(deltas, k=len(deltas))) / len(deltas)
                       for _ in range(draws))
    return dict(
        expressions=len(left), scenes=len(scenes), scene_rates=rates,
        scene_balanced_delta=sum(deltas) / len(deltas),
        scene_bootstrap_percentile_95=(
            [bootstrap[int(.025 * (draws - 1))],
             bootstrap[int(.975 * (draws - 1))]] if len(scenes) > 1 else None),
        fixed=sum(not a and b for values in scenes.values() for a, b in values),
        broken=sum(a and not b for values in scenes.values() for a, b in values),
        limitations=[
            "Superpoint success at IoU > .5 is not goal mIoU.",
            "Scene bootstrap is descriptive and unstable with few scenes.",
            "Matching integer support alone does not certify identical transforms.",
            "Caller must freeze sample, augmentation and model checkpoint identities.",
            "Self-comparison validates tooling only; not treatment efficacy."])
