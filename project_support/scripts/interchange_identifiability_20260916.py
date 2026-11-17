"""Static counterexamples only; no native data execution or model efficacy test."""
import hashlib
import itertools
import json
from pathlib import Path


def audit():
    # Scene features can already encode the target through the donor language.
    labels = (0, 0, 1, 1)
    states = tuple((target, index) for index, target in enumerate(labels))
    permutations = [
        left + right
        for left in itertools.permutations((0, 1))
        for right in itertools.permutations((2, 3))
    ]
    shortcut_errors = sum(
        states[perm[i]][0] != labels[i]
        for perm in permutations for i in range(4)
    )
    assert shortcut_errors == 0
    # An unconstrained different-target donor changes the shortcut answer.
    crossed = (2, 3, 0, 1)
    crossed_errors = sum(states[crossed[i]][0] != labels[i] for i in range(4))
    assert crossed_errors == 4
    unequal_states = sum(states[0] != states[1] for _ in [0])
    assert unequal_states == 1 and states[0][0] == states[1][0]
    # Two causal explanations fit all observational rows with H=V.
    rows = ((0, 0), (1, 1))
    assert all(h == v for h, v in rows)
    language_model = lambda h, v: h
    visual_model = lambda h, v: v
    assert all(language_model(h, v) == visual_model(h, v) for h, v in rows)
    assert language_model(0, 1) != visual_model(0, 1)
    return {
        "scope": "stdlib static finite counterexamples; not native model/data execution",
        "physical-scene-state-interchange": {
            "within_target_permutations": len(permutations),
            "recipient_evaluations": len(permutations) * 4,
            "shortcut_errors": shortcut_errors,
            "different_target_errors": crossed_errors,
            "finding": "Correct same-target exchange predictions and harmful different-target controls do not identify recipient-language use. Donor states may encode target identity. This disproves a sufficient identification claim, not possible training benefit.",
        },
        "same-target-description-grounding": {
            "equal_outputs_unequal_states": bool(unequal_states),
            "finding": "Target-equivalent outputs do not imply equal latent scene representations. Nuisance description information can coexist with correct grounding. Same-target identity alone does not specify which hidden dimensions should be invariant.",
        },
        "same-forward-coverage-diagnosis": {
            "observational_rows": len(rows),
            "observational_agreement": True,
            "intervention_disagreement": True,
            "finding": "Covered outcomes and observational agreement cannot identify whether language or visual state determines a prediction. This is a logical counterexample, not a fitted explanation for the captured TRAIN failures; known head-architecture confounding remains.",
        },
        "tests_passed": 3,
        "limitations": [
            "No new native forward, backward, AMP, resource, VAL or training claim.",
            "Finite lookup construction demonstrates non-identification; it does not assert the actual network uses this shortcut.",
            "No universal pretrained hard-IoU improvement admission requirement.",
            "No new mechanism or prior-art novelty demonstrated.",
        ],
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = audit()
    inputs = (
        "scripts/interchange_identifiability_20260916.py",
        "pipeline/designs/exp_design_20260916-0243.md",
        "pipeline/reports/scene_interchange_summary_20260916.json",
        "pipeline/reports/same_target_support_summary_20260916.json",
        "pipeline/reports/baseline_matched_summary_20260916.json",
    )
    result["evidence"] = [
        {"path": p, "sha256": hashlib.sha256((root / p).read_bytes()).hexdigest()}
        for p in inputs
    ]
    output = root / "pipeline/reports/interchange_identifiability_20260916.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tests_passed": result["tests_passed"], "output": str(output)}))
