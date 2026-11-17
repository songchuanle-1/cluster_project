"""Paired, same-forward mask-target control for M95 criterion semantics."""

import math

from m95_repeated_gt_mask_contract_20260924 import mask_binding


def _bce(logits, target):
    return sum(max(x, 0.0) - x * y + math.log1p(math.exp(-abs(x)))
               for x, y in zip(logits, target)) / len(logits)


def _dice(logits, target):
    probabilities = [1.0 / (1.0 + math.exp(-x)) for x in logits]
    intersection = sum(p * y for p, y in zip(probabilities, target))
    return 1.0 - (2.0 * intersection + 1.0) / (
        sum(probabilities) + sum(target) + 1.0
    )


def _iou(logits, target):
    prediction = [x >= 0.0 for x in logits]
    intersection = sum(p and y for p, y in zip(prediction, target))
    union = sum(prediction) + sum(target) - intersection
    return intersection / (union + 1e-6)


def compare(matched_pairs, gt_masks, query_logits):
    """Mirror loss_masks for one expression, with its matched pairs held fixed.

    Score-head predictions and indicator labels are deliberately not inferred.
    Outputs are per-expression losses before num_boxes and layer weighting.
    """
    if not gt_masks or not matched_pairs or not query_logits:
        raise ValueError("Nonempty GT, pair and query axes required")
    width = len(gt_masks[0])
    if width == 0 or any(len(mask) != width or
                         any(type(y) not in (int, bool, float) or y not in (0, 1)
                             for y in mask) for mask in gt_masks):
        raise ValueError("Invalid binary GT masks")
    if any(len(logits) != width or
           any(type(x) not in (int, float) or not math.isfinite(x)
               for x in logits) for logits in query_logits):
        raise ValueError("Invalid query mask logits")
    if any(len(pair) != 2 or
           any(type(value) is not int for value in pair) or
           not 0 <= pair[0] < len(query_logits) for pair in matched_pairs):
        raise ValueError("Invalid matched query axis")
    gt_ids = [gt for _, gt in matched_pairs]
    binding = mask_binding(gt_ids, len(gt_masks))
    rows = []
    for position, (query, gt) in enumerate(matched_pairs):
        addressed = binding["addressed_mask_gt_ids"][position]
        logits = query_logits[query]
        original = gt_masks[addressed]
        correct = gt_masks[gt]
        old_iou, new_iou = _iou(logits, original), _iou(logits, correct)
        rows.append({
            "pair_position": position,
            "query": query,
            "matched_gt": gt,
            "addressed_gt": addressed,
            "identity_mismatch": addressed != gt,
            "mask_values_differ": original != correct,
            "original_bce": _bce(logits, original),
            "corrected_bce": _bce(logits, correct),
            "original_dice": _dice(logits, original),
            "corrected_dice": _dice(logits, correct),
            "original_score_target": old_iou,
            "corrected_score_target": new_iou,
            "original_score_eligible": old_iou > 0.5,
            "corrected_score_eligible": new_iou > 0.5,
        })
    return {
        "pair_count": len(rows),
        "identity_mismatch_pairs": sum(row["identity_mismatch"] for row in rows),
        "changed_mask_pairs": sum(row["mask_values_differ"] for row in rows),
        "score_filter_crossings": sum(
            row["original_score_eligible"] != row["corrected_score_eligible"]
            for row in rows
        ),
        "original_bce": sum(row["original_bce"] for row in rows) / len(rows),
        "corrected_bce": sum(row["corrected_bce"] for row in rows) / len(rows),
        "original_dice": sum(row["original_dice"] for row in rows) / len(rows),
        "corrected_dice": sum(row["corrected_dice"] for row in rows) / len(rows),
        "pairs": rows,
        "score_mse": None,
        "indicator_loss": None,
    }
