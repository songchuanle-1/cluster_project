"""Frozen physical distractor identity across two native transforms."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRST = ROOT / "pipeline/reports/m95_seed_exact_1999_20260927.json"
SECOND = ROOT / "pipeline/reports/m95_seed_exact_2000_20260927.json"
FIRST_SHA = "1dc93b87cf42526f5608fdd74641c949f58bf0fe3b7cc8a5cb90b1960110cbe7"
SECOND_SHA = "4765c45afa2706ddb949020ffab4226214eef80655c19abd5e6af3b19b5a5910"


def analyze(first, second):
    if (first["checkpoint_sha256"] != second["checkpoint_sha256"]
            or first["population_manifest_sha256"] != second["population_manifest_sha256"]
            or first["transform_seed"] != 1999 or second["transform_seed"] != 2000):
        raise ValueError("Frozen native provenance differs")
    maps = []
    for source in (first, second):
        mapping = {}
        for row in source["rows"]:
            key = (row["scene"], row["ann_id"])
            if key in mapping:
                raise ValueError("Duplicate native expression")
            mapping[key] = row
        if len(mapping) != 128:
            raise ValueError("Frozen population changed")
        maps.append(mapping)
    if set(maps[0]) != set(maps[1]):
        raise ValueError("Native identity set differs")
    groups = defaultdict(list)
    for key in sorted(maps[0]):
        a, b = (mapping[key] for mapping in maps)
        if a["batch_input_sha256"] == b["batch_input_sha256"]:
            raise ValueError("Independent transform fingerprint unchanged")
        if a["target_instances"] != b["target_instances"]:
            raise ValueError("Target physical instance changed")
        afail, bfail = (r["selected_mask_iou"] <= .5 for r in (a, b))
        acontext, bcontext = (
            bool(r["selected_seed_is_context"]) and r["selected_mask_iou"] <= .5
            for r in (a, b))
        if acontext and bcontext:
            arm = "persistent_context_failure"
        elif afail and bfail and not acontext and not bcontext:
            arm = "persistent_other_failure"
        elif afail and bfail:
            arm = "mixed_failure"
        else:
            arm = "not_persistent_failure"
        if arm != "not_persistent_failure":
            groups[arm].append({
                "scene": key[0], "ann_id": key[1],
                "same_selected_instance": (
                    a["selected_seed_instance"] == b["selected_seed_instance"]),
                "selected_instances": [
                    a["selected_seed_instance"], b["selected_seed_instance"]],
            })
    return {
        "contract": "m95_distractor_identity_repeat_v1",
        "admission": False,
        "source_sha256": [FIRST_SHA, SECOND_SHA],
        "arms": {
            name: {
                "expressions": len(groups[name]),
                "scenes": len({r["scene"] for r in groups[name]}),
                "same_selected_instance": sum(r["same_selected_instance"] for r in groups[name]),
                "rows": groups[name],
            } for name in ("persistent_context_failure",
                           "persistent_other_failure", "mixed_failure")},
        "paired_scenes": sorted(
            set(r["scene"] for r in groups["persistent_context_failure"])
            & set(r["scene"] for r in groups["persistent_other_failure"])),
        "limits": "Observational TRAIN repeat; no distinct mechanism, causal intervention, admission or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or any(
            hashlib.sha256(path.read_bytes()).hexdigest() != sha
            for path, sha in ((FIRST, FIRST_SHA), (SECOND, SECOND_SHA))):
        raise ValueError("Output exists or frozen source differs")
    result = analyze(json.loads(FIRST.read_text(encoding="utf-8")),
                     json.loads(SECOND.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({name: {key: value for key, value in arm.items()
                              if key != "rows"} for name, arm in result["arms"].items()}))


if __name__ == "__main__":
    main()
