"""Finalize the preregistered noisy-OR bag operating-regime rejection."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "pipeline/reports"
SOURCE = REPORT / "m95_instance_bag_regime_20260927.json"
PREREG = REPORT / "m95_instance_bag_operating_regime_prereg_20260927.md"
OUTPUT = REPORT / "m95_instance_bag_regime_summary_20260927.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUTPUT.exists():
        raise ValueError("Output already exists")
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    if (len(data["bag_intervention"]) != 16 or len(data["rows"]) != 128
            or len(data["population_selected"]) != 32
            or data["transform_seed"] != 1999):
        raise ValueError("Population contract differs")
    bags = [bag for batch in data["bag_intervention"]
            for expression in batch["bag_regimes"] for bag in expression]
    if not bags:
        raise ValueError("No physical instance bags")
    probabilities = sorted(bag["probability"] for bag in bags)
    above = sum(bag["probability"] > .25 for bag in bags)
    suppress = sum(bag["member_grad_positive"] > 0 for bag in bags)
    zero = sum(bag["member_grad_abs_sum"] == 0 for bag in bags)
    negative = sum(bag["member_grad_negative"] > 0 for bag in bags)
    result = {
        "contract": "m95_instance_bag_regime_summary_v1",
        "admission": False,
        "source_sha256": sha(SOURCE),
        "prereg_sha256": sha(PREREG),
        "bags": len(bags),
        "probability_above_target": above,
        "positive_member_gradient_bags": suppress,
        "zero_member_gradient_bags": zero,
        "negative_member_gradient_bags": negative,
        "median_probability": probabilities[len(probabilities) // 2],
        "mean_bag_size": sum(bag["size"] for bag in bags) / len(bags),
        "rejection_gate_passed": above > len(bags) / 2
                                  and suppress > len(bags) / 2,
        "decision": (
            "Reject noisy-OR with focal target 0.25 as a constructive "
            "instance-context evidence mechanism. A positive derivative "
            "means gradient descent suppresses member logits. Do not "
            "retarget this same bag objective without a new derivation "
            "and matched control."
        ),
        "limitations": (
            "This disconfirms this proposed bag formulation, not the "
            "underlying physical context exposure. A backward-only "
            "diagnostic does not establish trained task efficacy."
        ),
    }
    if not result["rejection_gate_passed"]:
        raise ValueError("Preregistered rejection gate not met")
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "bags", "probability_above_target",
        "positive_member_gradient_bags", "zero_member_gradient_bags",
        "median_probability", "rejection_gate_passed")}))


if __name__ == "__main__":
    main()
