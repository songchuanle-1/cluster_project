"""Cross-check frozen supervision failures against source-bound matcher facts."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTITION = "pipeline/reports/m95_failure_partition_20260923-0318.json"
DISCORDANCE = "pipeline/reports/m95_discordance_provenance_20260923-1107.json"
LOSS = (
    "Cluster/framework/model/Quard_model/"
    "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/loss.py"
)
EXPECTED = {
    PARTITION: "491492118b2f55d78c02bc023f8e1e9408bd359eb5ef2af8824faee6bff6b5ee",
    DISCORDANCE: "6ed69abe4d26a2bd20283bb59119c2ebf30d4c0e73e2252903c210925292e372",
    LOSS: "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5",
}
EXCLUSION = "recoverable_positive_set_excludes_acceptable"
WITHIN = "recoverable_within_positive_score_failure"


def analyze(partition, discordance):
    if (partition.get("contract") != "m95_failure_partition_descriptive_v1"
            or discordance.get("admission") is not False
            or partition.get("admission") is not False):
        raise ValueError("Wrong frozen source contract")
    rows = partition["rows"]
    if len(rows) != 256 or {r["manifest_index"] for r in rows} != set(range(256)):
        raise ValueError("Incomplete frozen manifest")
    classes = {}
    for item in discordance["rows"]:
        index = item["manifest_index"]
        if index not in range(256) or item["query_count"] != len(item["seeds"]):
            raise ValueError("Invalid discordance class")
        if item["positive_outside_seed_count"] != sum(
            seed["positive"] and not seed["inside_target"] for seed in item["seeds"]
        ):
            raise ValueError("Outside-seed count differs")
        classes.setdefault(index, []).append(item)
    result = {}
    for label in (EXCLUSION, WITHIN):
        focus = [r for r in rows if r["partition"] == label]
        items = []
        for row in focus:
            index = row["manifest_index"]
            matches = classes.get(index, [])
            if label == EXCLUSION and (
                row["acceptable_queries"] <= 0
                or row["acceptable_native_positive_queries"] != 0
            ):
                raise ValueError("Exclusion partition contradicts native labels")
            if label == WITHIN and row["acceptable_native_positive_queries"] <= 0:
                raise ValueError("Within-positive partition contradicts native labels")
            outside = sum(c["positive_outside_seed_count"] for c in matches)
            if outside > row["native_positive_queries"]:
                raise ValueError("Discordance positives exceed query positives")
            items.append({
                "manifest_index": index,
                "scene_id": row["scene_id"],
                "native_positive_queries": row["native_positive_queries"],
                "acceptable_queries": row["acceptable_queries"],
                "acceptable_native_positive_queries": row["acceptable_native_positive_queries"],
                "target_seed_selector_available": row["target_seed_query"] is not None,
                "common_support": row["common_support"],
                "discordant_classes_saved": len(matches),
                "positive_outside_target_seed_in_saved_classes": outside,
                "matcher_cause_observed": False,
            })
        result[label] = {
            "expressions": len(items),
            "scenes": len({r["scene_id"] for r in items}),
            "target_seed_selector_available": sum(r["target_seed_selector_available"] for r in items),
            "common_support": sum(r["common_support"] for r in items),
            "rows_with_saved_outside_seed_positive": sum(
                r["positive_outside_target_seed_in_saved_classes"] > 0 for r in items
            ),
            "native_positive_queries": sum(r["native_positive_queries"] for r in items),
            "rows": items,
        }
    if result[EXCLUSION]["expressions"] != 6 or result[WITHIN]["expressions"] != 7:
        raise ValueError("Focus denominator differs")
    return {
        "contract": "m95_supervision_cause_boundary_v1",
        "scope": "Frozen outcome-selected TRAIN partition; source/static audit only",
        "groups": result,
        "source_contract": (
            "Criterion match_sampled_ins first marks nearest sampled query per GT, "
            "then instance-member queries excluding all nearest indices; loss_indi "
            "marks their union positive. Source does not identify saved per-query cause."
        ),
        "interpretation": (
            "Target-seed selector availability is not target-instance positive support "
            "or an any-instance objectness control. Saved outside-target-seed positives "
            "cannot be called erroneous without native nearest/member cause and GT binding."
        ),
        "limitations": [
            "Discordance classes are a partial, outcome-selected subset; absence is not absence of discordance.",
            "The saved partition does not identify per-query native nearest/member attribution.",
            "No native model forward/backward, matched objectness/listwise intervention, resource measurement or efficacy.",
        ],
        "native_execution_completed": False,
        "admission": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    evidence = []
    for path, expected in EXPECTED.items():
        digest = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        if digest != expected:
            raise ValueError("Frozen input differs: " + path)
        evidence.append({"path": path, "sha256": digest})
    result = analyze(
        json.loads((ROOT / PARTITION).read_text(encoding="utf-8")),
        json.loads((ROOT / DISCORDANCE).read_text(encoding="utf-8")),
    )
    result["evidence"] = evidence
    with Path(args.output).open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
