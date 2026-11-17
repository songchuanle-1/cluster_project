"""Static diagnostic adapter; all arrays must share the native support axis."""
from collections import Counter
from numbers import Integral

from capture_support_20260916 import support_record


def mask_endpoints(axis, selected_mask, instance_labels, target_instances,
                   semantic_labels=None):
    """Preserve every instance overlap, including background and tied endpoints."""
    support_record(axis["original_superpoint_ids"], axis["sample_inverse"])
    n = len(axis["original_superpoint_ids"])
    if len(selected_mask) != n or len(instance_labels) != n:
        raise ValueError("Mask/instance support mismatch")
    if any(type(x) is not bool for x in selected_mask):
        raise ValueError("Require thresholded boolean mask")
    if any(not isinstance(x, Integral) or isinstance(x, bool) for x in instance_labels):
        raise ValueError("Require integer physical instance labels")
    targets = set(target_instances)
    if not targets or any(not isinstance(x, Integral) or isinstance(x, bool)
                          or x < 0 for x in targets):
        raise ValueError("Require nonnegative physical target IDs")
    counts = Counter(instance_labels)
    if not targets.issubset(counts):
        raise ValueError("Target absent from captured support")
    semantics = None
    if semantic_labels is not None:
        if len(semantic_labels) != n:
            raise ValueError("Semantic support mismatch")
        if any(not isinstance(x, Integral) or isinstance(x, bool) for x in semantic_labels):
            raise ValueError("Require integer semantic labels")
        semantics = {}
        for instance in counts:
            values = {semantic_labels[i] for i in range(n) if instance_labels[i] == instance}
            # Do not invent a class by taking the majority of a mixed instance.
            semantics[instance] = next(iter(values)) if len(values) == 1 else None
    selected = sum(selected_mask)
    intersections = Counter(label for label, keep in zip(instance_labels, selected_mask) if keep)
    overlaps = [
        dict(instance=int(label), intersection=intersections[label],
             union=selected + counts[label] - intersections[label],
             iou=intersections[label] / (selected + counts[label] - intersections[label]),
             semantic_class=None if semantics is None else semantics[label])
        for label in sorted(counts) if label >= 0
    ]
    maximum = max((r["iou"] for r in overlaps), default=0.)
    winners = [r["instance"] for r in overlaps if maximum > 0 and r["iou"] == maximum]
    target_classes = None if semantics is None else {semantics[t] for t in targets}
    same_class = None
    if len(winners) == 1 and target_classes is not None:
        cls = semantics[winners[0]]
        if (cls is not None and cls >= 0 and None not in target_classes
                and all(c >= 0 for c in target_classes)):
            same_class = cls in target_classes
    return dict(selected_superpoints=selected,
                selected_background=sum(v for k, v in intersections.items() if k < 0),
                overlaps=overlaps, best_overlap_instances=winners,
                unique_wrong_instance=(len(winners) == 1 and winners[0] not in targets),
                same_class=same_class,
                semantic_available=semantics is not None,
                metric="unweighted superpoint IoU, not point IoU or goal mIoU")


def recoverable_same_class_stratum(query_ious, selected_query, endpoints):
    if not query_ious or not 0 <= selected_query < len(query_ious):
        raise ValueError("Invalid query axis")
    import math
    if any(not math.isfinite(x) or not 0 <= x <= 1 for x in query_ious):
        raise ValueError("Invalid query IoU")
    return (max(query_ious) > .5 and query_ious[selected_query] <= .5
            and endpoints["unique_wrong_instance"]
            and endpoints["same_class"] is True)
