"""Static audit of archived TRAIN summaries and finite identifying controls."""
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def identity(pair):
    return (pair["scene"], tuple(pair["target_ids"]), tuple(pair["ann_ids"]))


def finite_controls():
    # One common support and readout; only the causal rule differs.
    readout = lambda state: state[0]
    recipient = lambda language, donor, nuisance: (language, nuisance)
    shortcut = lambda language, donor, nuisance: (donor, nuisance)
    harmless = lambda language, donor, nuisance: (0, language + nuisance)
    cells = list(itertools.product((0, 1), repeat=3))
    disagreements = sum(
        readout(recipient(*cell)) != readout(shortcut(*cell)) for cell in cells
    )
    assert disagreements == 4
    for donor, nuisance in itertools.product((0, 1), repeat=2):
        assert readout(recipient(0, donor, nuisance)) != readout(recipient(1, donor, nuisance))
        assert readout(shortcut(0, donor, nuisance)) == readout(shortcut(1, donor, nuisance))
        assert harmless(0, donor, nuisance) != harmless(1, donor, nuisance)
        assert readout(harmless(0, donor, nuisance)) == readout(harmless(1, donor, nuisance))
    # Different-target language contrasts, not same-target equivalence, identify
    # these two rules. A recipient-insensitive constant can fit a same-target pair.
    same_target_labels = (0, 0)
    assert all(readout(harmless(l, 0, 0)) == y for l, y in enumerate(same_target_labels))
    # Additive fusion is non-injective even without destructive cancellation.
    a, b = ((2, 0), (0, 2)), ((0, 2), (2, 0))
    fuse = lambda pair: tuple(x + y for x, y in zip(*pair))
    dot = lambda pair: sum(x * y for x, y in zip(*pair))
    assert fuse(a) == fuse(b) == (2, 2)
    assert dot(a) == dot(b) == 0
    assert a[0][0] > a[1][0] and b[0][0] < b[1][0]
    return {
        "factorial_cells": len(cells),
        "recipient_vs_donor_rule_disagreements": disagreements,
        "fixed_donor_language_contrasts": 4,
        "nuisance_only_contrasts_with_unchanged_output": 4,
        "same_target_constant_shortcut_correct": 2,
        "modality_noninjectivity": {"first": a, "second": b, "same_sum": fuse(a), "same_dot": 0},
        "conclusion": (
            "A crossed recipient-language/donor-state table separates the specified "
            "recipient and donor rules at fixed readout/support; hidden-state change alone "
            "does not. Same-target labels cannot require different outputs. Equal fused "
            "sum and cancellation statistic do not identify modality correspondence."
        ),
    }


def audit():
    text_path = ROOT / "pipeline/reports/same_target_summary_20260916_metadata_corrected.json"
    support_path = ROOT / "pipeline/reports/same_target_support_summary_20260916.json"
    corrected = json.loads(text_path.read_text(encoding="utf-8"))
    support = json.loads(support_path.read_text(encoding="utf-8"))
    indices = {}
    for branch, value in support["branches"].items():
        pairs = value["pairs"]
        indices[branch] = {identity(pair): pair for pair in pairs}
        assert len(indices[branch]) == len(pairs) == 64
    assert len(corrected["pairs"]) == 64
    assert len({identity(pair) for pair in corrected["pairs"]}) == 64
    assert all(set(index) == set(indices["base"]) for index in indices.values())
    rows = []
    for pair in corrected["pairs"]:
        key = identity(pair)
        assert key in indices["base"]
        assert pair["ious"] == indices["base"][key]["ious"]
        if not pair["success_disagreement"]:
            continue
        rows.append({
            "scene": pair["scene"], "target_ids": pair["target_ids"],
            "ann_ids": pair["ann_ids"], "corrected_utterances": pair["utterances"],
            "observable_identity_contrast": pair["winner_observable"],
            "branch_results": {
                branch: {field: index[key][field] for field in
                         ("winner_ids", "ious", "success_disagreement")}
                for branch, index in indices.items()
            },
            "semantic_equivalence": "unverified",
            "predicate_truth": "unavailable; cannot attribute to color, relation or viewpoint",
        })
    assert len(rows) == 8
    assert sum(row["observable_identity_contrast"] for row in rows) == 6
    assert all(all(v["success_disagreement"] for v in row["branch_results"].values()) for row in rows)
    return {
        "scope": "Local static analysis of completed TRAIN artifacts; no native replay.",
        "pairs_joined": 64, "expressions": 128, "scenes": 32,
        "persistent_disagreements": rows,
        "finite_controls": finite_controls(),
        "checks": {
            "unique_identity_joins": True, "all_branch_keysets_equal": True,
            "base_iou_preserved": True, "all_eight_disagreements_persist": True,
            "observable_partition_six_two": True, "factorial_rule_separation": True,
            "latent_nuisance_negative_control": True, "modality_collision": True,
        },
        "interpretation": [
            "Completed fixed-support evidence establishes output dependence across some descriptions, not correctness of the textual predicates.",
            "The finite factorial test separates only the specified rules, not arbitrary native networks or memorization shortcuts.",
            "Do not rerun rejected interchange: its native read-only/mask-only path controls are complete.",
            "For a future distinct mechanism, predefine language-relevant output contrasts and nuisance controls with fixed weights, support and mask readout.",
            "Modality sum non-injectivity is mathematical, not evidence that these collisions occur in captured data or that a new fusion operator is novel.",
        ],
        "next_actions": {
            "same-target-description-grounding": "Use these eight keyed text/support records as a bounded error set. Establish predicate truth from already available scene metadata before assigning relation/attribute causality; no semantic-equivalence label from target identity.",
            "same-forward-coverage-diagnosis": "Finite identifying control complete for recipient/donor/nuisance countermodels. Require a distinct mechanism with an observable task contrast and no direct mask replacement; do not repeat rejected interchange or coverage capture.",
            "input-modality-distinguishability": "Non-injective fusion is not sufficient motivation. Derive a task-specific correspondence variable observable in existing paired input evidence before any fusion proposal; no magnitude weighting or generic tensor product.",
        },
        "limitations": [
            "Not a new model, native causal result, backward/resource test, VAL result or novelty claim.",
            "Fixed TRAIN selection and strict IoU>.5 inherited; no population confidence claim.",
            "No mechanism is admitted; three free queue slots remain a scientific gap.",
        ],
        "evidence": [
            {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in (text_path, support_path, Path(__file__))
        ],
    }


if __name__ == "__main__":
    result = audit()
    output = ROOT / "pipeline/reports/recipient_dependence_audit_20260916.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks_passed": len(result["checks"]), "pairs": result["pairs_joined"],
                      "persistent_disagreements": len(result["persistent_disagreements"]),
                      "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}))
