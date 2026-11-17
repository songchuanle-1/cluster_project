"""Audit physical target-seed failure persistence in frozen native captures."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    (ROOT / "pipeline/reports/m95_seed_exact_1999_20260927.json",
     "1dc93b87cf42526f5608fdd74641c949f58bf0fe3b7cc8a5cb90b1960110cbe7"),
    (ROOT / "pipeline/reports/m95_seed_exact_2000_20260927.json",
     "4765c45afa2706ddb949020ffab4226214eef80655c19abd5e6af3b19b5a5910"),
)


def arm(row):
    if float(row["selected_mask_iou"]) > 0.5:
        return "success"
    if row["selected_seed_matches_target_instance"]:
        return "target_seed_failure"
    if row["selected_seed_is_context"]:
        return "context_failure"
    return "other_failure"


def analyze(first, second):
    if (first["checkpoint_sha256"] != second["checkpoint_sha256"]
            or first["population_manifest_sha256"] != second["population_manifest_sha256"]
            or first["transform_seed"] != 1999 or second["transform_seed"] != 2000):
        raise ValueError("Native provenance differs")
    maps = []
    for source in (first, second):
        rows = source["rows"]
        mapping = {(row["scene"], row["ann_id"]): row for row in rows}
        if len(rows) != 128 or len(mapping) != 128:
            raise ValueError("Native expression population differs")
        maps.append(mapping)
    if set(maps[0]) != set(maps[1]):
        raise ValueError("Expression identity sets differ")

    arms = ("target_seed_failure", "context_failure", "other_failure")
    occurrences = [defaultdict(list), defaultdict(list)]
    persistent = defaultdict(list)
    transitions = Counter()
    for key in sorted(maps[0]):
        a, b = (mapping[key] for mapping in maps)
        if (a["batch_input_sha256"] == b["batch_input_sha256"]
                or a["target_instances"] != b["target_instances"]):
            raise ValueError("Transform fingerprint or target physical ID differs")
        for row in (a, b):
            if not 0 <= float(row["selected_mask_iou"]) <= 1:
                raise ValueError("Selected IoU out of range")
            if (row["selected_seed_matches_target_instance"]
                    != (row["selected_seed_instance"] in row["target_instances"])):
                raise ValueError("Seed physical target binding differs")
            if row["selected_seed_is_context"] and row["selected_seed_matches_target_instance"]:
                raise ValueError("Target seed is also non-target context")
        aa, bb = arm(a), arm(b)
        transitions[(aa, bb)] += 1
        for index, label in enumerate((aa, bb)):
            if label in arms:
                occurrences[index][label].append(key)
        if aa == bb and aa in arms:
            persistent[aa].append({
                "scene": key[0], "ann_id": key[1],
                "same_seed_instance": a["selected_seed_instance"] == b["selected_seed_instance"],
                "ious": [a["selected_mask_iou"], b["selected_mask_iou"]],
                "final_seed_labels": [a["selected_seed_final_target"],
                                      b["selected_seed_final_target"]],
            })
    return {
        "contract": "m95_target_seed_failure_v1",
        "admission": False,
        "source_sha256": [digest for _, digest in SOURCES],
        "population": {"expressions": 128, "scenes": len({key[0] for key in maps[0]})},
        "arms": {name: {
            "seed1999_expressions": len(occurrences[0][name]),
            "seed2000_expressions": len(occurrences[1][name]),
            "persistent_expressions": len(persistent[name]),
            "persistent_scenes": len({r["scene"] for r in persistent[name]}),
            "persistent_same_seed_instance": sum(r["same_seed_instance"]
                                                for r in persistent[name]),
            "persistent_rows": persistent[name],
        } for name in arms},
        "transitions": [
            {"first": a, "second": b, "expressions": count}
            for (a, b), count in sorted(transitions.items())],
        "limits": "Selected TRAIN cohort, observational only; no new causal mechanism, admission or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output already exists")
    for path, digest in SOURCES:
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("Frozen capture SHA256 differs")
    result = analyze(*(json.loads(path.read_text(encoding="utf-8"))
                       for path, _ in SOURCES))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({name: {k: v for k, v in data.items() if k != "persistent_rows"}
                      for name, data in result["arms"].items()}))


if __name__ == "__main__":
    main()
