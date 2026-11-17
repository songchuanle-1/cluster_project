"""Summarize the preregistered native bag-gradient specificity screen."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "pipeline/reports"
SOURCE = REPORT / "m95_instance_bag_population_20260927.json"
PREREG = REPORT / "m95_instance_bag_population_prereg_20260927.md"
OUTPUT = REPORT / "m95_instance_bag_population_summary_20260927.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUTPUT.exists():
        raise ValueError("Summary already exists")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    bags = source["bag_intervention"]
    if (len(bags) != 16 or len(source["rows"]) != 128
            or len(source["population_selected"]) != 32
            or source["transform_seed"] != 1999):
        raise ValueError("Population contract differs")
    batches = []
    for index, entry in enumerate(bags):
        coverage = entry["coverage"]
        moved = sum(x["seeds_moved_to_other_bags"] for x in coverage)
        eligible = sum(x["eligible_seeds"] for x in coverage)
        physical = entry["gradient_delta_l1"]["physical_vs_shuffled"]
        hard_zero = entry["gradient_delta_l1"]["physical_vs_hard_zero"]
        if (entry["parameter_tensors"] != 2 or hard_zero <= 0
                or not 0 <= moved <= eligible):
            raise ValueError("Invalid native gradient or mixing")
        batches.append({
            "index": index,
            "eligible_seeds": eligible,
            "moved_seeds": moved,
            "groups": sum(x["groups_at_least_two"] for x in coverage),
            "physical_vs_shuffled_gradient_l1": physical,
            "physical_vs_hard_zero_gradient_l1": hard_zero,
            "identity_specificity_ratio": physical / hard_zero,
        })
    result = {
        "contract": "m95_instance_bag_population_summary_v1",
        "admission": False,
        "source_sha256": sha(SOURCE),
        "prereg_sha256": sha(PREREG),
        "batches": batches,
        "total_eligible_seeds": sum(x["eligible_seeds"] for x in batches),
        "total_moved_seeds": sum(x["moved_seeds"] for x in batches),
        "ratio_below_0_1": sum(x["identity_specificity_ratio"] < .1
                               for x in batches),
        "ratio_at_least_0_5": sum(x["identity_specificity_ratio"] >= .5
                                  for x in batches),
        "ratio_at_least_1": sum(x["identity_specificity_ratio"] >= 1
                                for x in batches),
        "limits": (
            "Mixed identity-specific gradient differences under a shuffled "
            "bag control on an unchanged checkpoint. Neither magnitude nor "
            "ratio establishes task efficacy or novelty. The per-batch "
            "parameter gradients aggregate expressions and can be dominated "
            "by group count/score distributions. No new model backward, "
            "trained intervention, uniform resource gate or admission."
        ),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "total_eligible_seeds", "total_moved_seeds", "ratio_below_0_1",
        "ratio_at_least_0_5", "ratio_at_least_1")}))


if __name__ == "__main__":
    main()
