"""Size-matched control for frozen M95 query-mask frequency diagnosis."""
import argparse
import hashlib
import json
import math
from pathlib import Path

FREQUENCY_SHA = "3822e7f7a682a6ee932b4efccbdcb7616e1b9738d0c025a16de5ad2c44cd008d"


def analyze(report):
    limited = [r for r in report["groups"]["limited"]["rows"]
               if "target_minus_competitor" in r]
    covered = {r["manifest_index"]: r for r in report["groups"]["covered"]["rows"]
               if "target_minus_competitor" in r}
    if len(limited) != 16 or len(covered) != 189:
        raise ValueError("Frozen eligible population differs")
    matched = []
    for item in sorted(limited, key=lambda r: r["manifest_index"]):
        def cost(control):
            return (
                item["scene"] != control["scene"],
                abs(math.log1p(item["target_superpoints"])
                    - math.log1p(control["target_superpoints"]))
                + abs(math.log1p(item["competitor_superpoints"])
                      - math.log1p(control["competitor_superpoints"])),
                control["manifest_index"],
            )
        control = min(covered.values(), key=cost)
        del covered[control["manifest_index"]]
        matched.append({
            "limited_index": item["manifest_index"],
            "control_index": control["manifest_index"],
            "limited_scene": item["scene"],
            "control_scene": control["scene"],
            "target_size": [item["target_superpoints"], control["target_superpoints"]],
            "competitor_size": [item["competitor_superpoints"], control["competitor_superpoints"]],
            "delta_target_frequency": item["target_frequency"] - control["target_frequency"],
            "delta_competitor_frequency": item["competitor_frequency"] - control["competitor_frequency"],
            "delta_contrast": (item["target_minus_competitor"]
                               - control["target_minus_competitor"]),
        })
    keys = ("delta_target_frequency", "delta_competitor_frequency", "delta_contrast")
    return {
        "contract": "m95_frequency_size_control_v1",
        "admission": False,
        "source_sha256": FREQUENCY_SHA,
        "pairs": matched,
        "summary": {
            "pairs": len(matched),
            "limited_scenes": len({r["limited_scene"] for r in matched}),
            "same_scene_pairs": sum(r["limited_scene"] == r["control_scene"] for r in matched),
            **{key: {
                "mean": sum(r[key] for r in matched) / len(matched),
                "negative": sum(r[key] < 0 for r in matched),
            } for key in keys},
        },
        "limits": "Retrospective frozen TRAIN matching; size control does not establish a new method or efficacy.",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--frequency", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    data = args.frequency.read_bytes()
    if hashlib.sha256(data).hexdigest() != FREQUENCY_SHA:
        raise ValueError("Frozen frequency report differs")
    report = analyze(json.loads(data))
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    main()
