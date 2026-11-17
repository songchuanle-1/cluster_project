"""Check independently captured M95 matcher causes without running the model.

Input rows must come from the native criterion call, not hierarchy FPS positions.
The checker verifies attribution; it does not infer that a training label is
semantically correct or that a proposed intervention improves validation mIoU.
"""

import math
from collections import Counter


def check_row(row):
    positions = row["sampled_pos"]
    centroids = row["obj_pos"]
    labels = row["sampled_instance_labels"]
    object_ids = row["object_ids"]
    nearest = row["nearest_query_per_gt"]
    members = row["member_queries_per_gt"]
    positive = row["native_positive"]
    n, g = len(positions), len(centroids)
    if not n or not g or len(labels) != n or len(positive) != n:
        raise ValueError("Inconsistent nonempty query axis")
    if len(object_ids) != g or len(nearest) != g or len(members) != g:
        raise ValueError("Inconsistent GT axis")
    if len(set(object_ids)) != g:
        raise ValueError("Duplicate native object ID")
    if any(len(p) != 3 or not all(math.isfinite(float(x)) for x in p)
           for p in positions + centroids):
        raise ValueError("Nonfinite or malformed native coordinate")
    if any(type(q) is not int or q < 0 or q >= n for q in nearest):
        raise ValueError("Invalid nearest query index")
    if any(type(value) is not bool for value in positive):
        raise ValueError("Invalid positive label")

    nearest_set = set(nearest)
    for gt, q in enumerate(nearest):
        distances = [math.dist(p, centroids[gt]) for p in positions]
        if not math.isclose(distances[q], min(distances), abs_tol=1e-5):
            raise ValueError("Native nearest query contradicts coordinates")
    cause = [set() for _ in range(n)]
    for q in nearest:
        cause[q].add("nearest_gt")
    for gt, group in enumerate(members):
        if len(set(group)) != len(group):
            raise ValueError("Duplicate membership index")
        expected = {
            q for q, label in enumerate(labels)
            if label == object_ids[gt] and q not in nearest_set
        }
        if set(group) != expected:
            raise ValueError("Native membership contradicts sampled labels")
        for q in group:
            cause[q].add("instance_member")
    if [bool(tags) for tags in cause] != positive:
        raise ValueError("Positive vector contradicts native matcher causes")
    return dict(Counter(
        "+".join(sorted(tags)) if tags else "negative" for tags in cause
    ))
