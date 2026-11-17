"""Audit the native criterion's repeated-GT mask indexing without model execution."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOSS = (
    "Cluster/framework/model/Quard_model/"
    "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/loss.py"
)
LOSS_SHA256 = "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5"


def mask_binding(matched_gt_ids, n_gt):
    """Return original GT identities addressed by target['masks'][idx_gt]."""
    if n_gt < 1 or any(type(g) is not int or g < 0 or g >= n_gt for g in matched_gt_ids):
        raise ValueError("Invalid native GT axis")
    counts = [matched_gt_ids.count(g) for g in range(n_gt)]
    if not all(counts):
        raise ValueError("Native matcher must assign at least one query per GT")
    expanded = [g for g, count in enumerate(counts) for _ in range(count)]
    addressed = [expanded[g] for g in matched_gt_ids]
    return {
        "counts": counts,
        "matched_gt_ids": matched_gt_ids,
        "expanded_mask_gt_ids": expanded,
        "addressed_mask_gt_ids": addressed,
        "mismatched_pair_positions": [
            i for i, (expected, actual) in enumerate(zip(matched_gt_ids, addressed))
            if expected != actual
        ],
    }


def mismatch_from_counts(counts):
    """Predict per-GT wrong-mask pairs from match counts, independent of pair order."""
    if not counts or any(type(count) is not int or count < 1 for count in counts):
        raise ValueError("Each GT needs a positive integer match count")
    extra_before = 0
    wrong_pairs = []
    for count in counts:
        wrong_pairs.append(count if extra_before else 0)
        extra_before += count - 1
    return wrong_pairs


def audit():
    loss_hash = hashlib.sha256((ROOT / LOSS).read_bytes()).hexdigest()
    if loss_hash != LOSS_SHA256:
        raise ValueError("M95 loss source differs from reviewed version")
    examples = {
        "single_gt_multiple_matches": mask_binding([0, 0, 0], 1),
        "two_gt_one_match_each": mask_binding([0, 1], 2),
        "two_gt_extra_first": mask_binding([0, 1, 0], 2),
        "two_gt_extra_second": mask_binding([0, 1, 1], 2),
        "three_gt_extra_first": mask_binding([0, 1, 2, 0], 3),
    }
    return {
        "contract": "m95_repeated_gt_mask_contract_v1",
        "scope": "Source-bound conditional indexing audit; synthetic GT assignments only",
        "examples": examples,
        "source": {"path": LOSS, "sha256": loss_hash},
        "finding": (
            "The criterion expands target masks by per-GT match count but indexes "
            "the expanded masks with unexpanded GT IDs. For some multi-GT count "
            "patterns, a (query, GT) pair receives another GT's mask."
        ),
        "limitations": (
            "No native multi-GT frequency or affected frozen expression is known; "
            "no model forward, gradient, resource or efficacy measurement."
        ),
        "admission": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with Path(args.output).open("x", encoding="utf-8") as handle:
        json.dump(audit(), handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
