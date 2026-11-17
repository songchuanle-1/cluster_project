"""Bounded control support audit of the frozen M95 TRAIN partition."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

SOURCE_SHA256 = "491492118b2f55d78c02bc023f8e1e9408bd359eb5ef2af8824faee6bff6b5ee"
PARTITIONS = (
    "deployed_success",
    "no_acceptable_query",
    "recoverable_positive_selector_repairs",
    "recoverable_positive_set_excludes_acceptable",
    "recoverable_within_positive_score_failure",
)


def audit(document):
    if (document.get("contract") != "m95_failure_partition_descriptive_v1"
            or document.get("admission") is not False):
        raise ValueError("Wrong frozen source contract")
    rows = document["rows"]
    if len(rows) != 256 or {r["manifest_index"] for r in rows} != set(range(256)):
        raise ValueError("Incomplete or duplicated frozen manifest")
    if Counter(r["stratum"] for r in rows) != {"ambiguous": 128, "class_unique": 128}:
        raise ValueError("Manifest strata differ")
    if any(r["partition"] not in PARTITIONS for r in rows):
        raise ValueError("Unknown failure partition")
    groups = {}
    for name in PARTITIONS:
        group = [r for r in rows if r["partition"] == name]
        for r in group:
            a, p = r["acceptable_queries"], r["acceptable_native_positive_queries"]
            if not (type(a) is int and type(p) is int and 0 <= p <= a):
                raise ValueError("Invalid acceptable query counts")
            if type(r["positive_set_equals_target_seed_set"]) is not bool:
                raise ValueError("Missing target-seed control")
            if type(r["common_support"]) is not bool:
                raise ValueError("Missing common-support control")
        groups[name] = {
            "expressions": len(group),
            "scenes": len({r["scene_id"] for r in group}),
            "acceptable_queries": sum(r["acceptable_queries"] for r in group),
            "acceptable_native_positives": sum(
                r["acceptable_native_positive_queries"] for r in group
            ),
            "native_positive_equals_target_seed_set": sum(
                r["positive_set_equals_target_seed_set"] for r in group
            ),
            "common_support": sum(r["common_support"] for r in group),
        }
    excluded = groups["recoverable_positive_set_excludes_acceptable"]
    within = groups["recoverable_within_positive_score_failure"]
    if (excluded["expressions"] != 6 or excluded["acceptable_native_positives"]
            or within["expressions"] != 7 or not within["acceptable_native_positives"]):
        raise ValueError("Frozen focus partition drift")
    return {
        "contract": "m95_supervision_partition_controls_v1",
        "scope": "Fixed 256 TRAIN expressions; descriptive partition, not efficacy",
        "groups": groups,
        "focus_expressions": excluded["expressions"] + within["expressions"],
        "focus_scenes": len({
            r["scene_id"] for r in rows if r["partition"] in (
                "recoverable_positive_set_excludes_acceptable",
                "recoverable_within_positive_score_failure",
            )
        }),
        "interpretation": [
            "Exclusion rows have no acceptable native-positive query; native binary labels cannot reward an acceptable query.",
            "Within-positive rows include acceptable positives, but a binary positive label alone does not order them against failed positives.",
            "Target-seed set equality is not the any-instance objectness control; neither is a matched training intervention.",
        ],
        "limitations": [
            "Acceptable queries and failure partitions use outcome IoU on TRAIN; query counts are not independent observations.",
            "No native matcher cause, query-state capture, matched backward, resource or validation result is supplied.",
            "No distinct supervision mechanism or admission follows from these counts.",
        ],
        "native_backward_executed": False,
        "admission": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(args.source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError("Frozen source hash differs")
    result = audit(json.loads(source.read_text(encoding="utf-8")))
    result["evidence"] = [{"path": str(source), "sha256": digest}]
    with Path(args.output).open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
