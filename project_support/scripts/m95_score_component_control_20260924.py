"""Frozen score-head controls over the existing fixed-pair mask replay."""

import math

from m95_mask_component_counterfactual_20260924 import compare as mask_compare


def _indicator_control(matched_pairs, query_scores):
    positive_queries = [query for query, _ in matched_pairs]
    if len(set(positive_queries)) != len(positive_queries):
        raise ValueError("Duplicate positive query in matched pairs")

    entropy = math.log(1.0 + 1e-6)
    positive_terms = []
    negative_terms = []
    for query, probability in enumerate(query_scores):
        if type(probability) not in (int, float):
            raise ValueError("Invalid frozen indicator probability")
        if not math.isfinite(probability) or not 0.0 < probability < 1.0:
            raise ValueError("Indicator probability must be finite and interior")
        if query in positive_queries:
            positive_terms.append(entropy - math.log(probability))
        else:
            negative_terms.append(entropy - math.log1p(-probability))

    eos_coef = 0.1
    numerator = sum(positive_terms) + eos_coef * sum(negative_terms)
    return {
        "eos_coef": eos_coef,
        "entropy_constant_per_query": entropy,
        "positive_queries": sorted(positive_queries),
        "positive_count": len(positive_terms),
        "negative_count": len(negative_terms),
        "numerator": numerator,
        "per_matched_pair": numerator / len(matched_pairs),
    }


def compare(matched_pairs, gt_masks, query_logits, query_scores=None):
    result = mask_compare(matched_pairs, gt_masks, query_logits)
    if query_scores is None:
        return result
    if len(query_scores) != len(query_logits) or any(
        type(score) not in (int, float) or not math.isfinite(score)
        for score in query_scores
    ):
        raise ValueError("Invalid frozen score predictions")

    def mse(target_key, eligible_key):
        rows = [row for row in result["pairs"] if row[eligible_key]]
        return (sum((query_scores[row["query"]] - row[target_key]) ** 2
                    for row in rows) / len(rows) if rows else 0.0)

    result["score_mse"] = {
        "original": mse("original_score_target", "original_score_eligible"),
        "corrected": mse("corrected_score_target", "corrected_score_eligible"),
        "original_eligible_pairs": sum(
            row["original_score_eligible"] for row in result["pairs"]
        ),
        "corrected_eligible_pairs": sum(
            row["corrected_score_eligible"] for row in result["pairs"]
        ),
    }
    result["indicator_loss"] = _indicator_control(matched_pairs, query_scores)
    return result
