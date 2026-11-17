"""Frozen category-and-size control for query-support frequency."""
import argparse
import hashlib
import json
import math
from pathlib import Path

FREQUENCY_SHA = "3822e7f7a682a6ee932b4efccbdcb7616e1b9738d0c025a16de5ad2c44cd008d"
FEATURE_SHA = "7537ade52ef41ea73582fe1452bfa410f0a17e5485634ef572769ba300fc4c81"


def read(path, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Frozen input differs: {path}")
    return json.loads(data)


def analyze(frequency, feature):
    if frequency["capture_sha256"] != feature["capture_sha256"]:
        raise ValueError("Capture identity differs")
    by_index = {
        row["manifest_index"]: row
        for group in ("limited", "covered")
        for row in feature[group]["rows"]
    }
    groups = {}
    for name, predicate in (("valid_category", lambda value: value >= 0),
                             ("unknown_category", lambda value: value == -100)):
        limited = [r for r in frequency["groups"]["limited"]["rows"]
                   if "target_minus_competitor" in r
                   and predicate(by_index[r["manifest_index"]]["category"])]
        controls = {r["manifest_index"]: r for r in frequency["groups"]["covered"]["rows"]
                    if "target_minus_competitor" in r
                    and predicate(by_index[r["manifest_index"]]["category"])}
        pairs = []
        for row in sorted(limited, key=lambda r: r["manifest_index"]):
            category = by_index[row["manifest_index"]]["category"]
            possible = [r for r in controls.values()
                        if by_index[r["manifest_index"]]["category"] == category]
            if not possible:
                continue
            def cost(other):
                return (
                    row["scene"] != other["scene"],
                    abs(math.log1p(row["target_superpoints"]) -
                        math.log1p(other["target_superpoints"]))
                    + abs(math.log1p(row["competitor_superpoints"]) -
                          math.log1p(other["competitor_superpoints"])),
                    other["manifest_index"],
                )
            control = min(possible, key=cost)
            del controls[control["manifest_index"]]
            pairs.append({
                "limited_index": row["manifest_index"],
                "control_index": control["manifest_index"],
                "category": category, "scene": row["scene"],
                "same_scene": row["scene"] == control["scene"],
                "target_sizes": [row["target_superpoints"], control["target_superpoints"]],
                "competitor_sizes": [row["competitor_superpoints"], control["competitor_superpoints"]],
                "delta_target": row["target_frequency"] - control["target_frequency"],
                "delta_competitor": row["competitor_frequency"] - control["competitor_frequency"],
                "delta_contrast": (row["target_minus_competitor"]
                                   - control["target_minus_competitor"]),
            })
        groups[name] = {
            "eligible_limited": len(limited), "pairs": len(pairs),
            "scenes": len({r["scene"] for r in pairs}),
            "same_scene_pairs": sum(r["same_scene"] for r in pairs),
            "mean_delta_contrast": (sum(r["delta_contrast"] for r in pairs) / len(pairs)
                                    if pairs else None),
            "negative_delta_contrast": sum(r["delta_contrast"] < 0 for r in pairs),
            "mean_delta_target": (sum(r["delta_target"] for r in pairs) / len(pairs)
                                  if pairs else None),
            "mean_delta_competitor": (sum(r["delta_competitor"] for r in pairs) / len(pairs)
                                      if pairs else None),
            "pairs_detail": pairs,
        }
    return {
        "contract": "m95_frequency_semantic_control_v1",
        "admission": False, "frequency_sha256": FREQUENCY_SHA, "feature_sha256": FEATURE_SHA,
        "groups": groups,
        "limits": "GT semantic category matches retrospective controls only; -100 invalid category separately reported. No native new-model control or trained efficacy.",
    }


def main():
    p = argparse.ArgumentParser()
    for key in ("frequency", "feature", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(read(args.frequency, FREQUENCY_SHA),
                     read(args.feature, FEATURE_SHA))
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: {n: v for n, v in g.items() if n != "pairs_detail"}
                      for k, g in report["groups"].items()}))


if __name__ == "__main__":
    main()
