"""Pair same-scene expressions by frozen M95 physical target identity."""
import argparse
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, MANIFEST_SHA, PRODUCER_SHA, CHECKPOINT_SHA, sha,
)


def analyze(capture):
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256):
        raise ValueError("Frozen provenance differs")
    scenes = defaultdict(list)
    seen = set()
    for row in capture["rows"]:
        index = row["manifest_index"]
        if index in seen or not row["target_instances"] or len(row["ious"]) != 128:
            raise ValueError("Row identity differs")
        seen.add(index)
        scenes[row["scene"]].append(row)
    if seen != set(range(256)):
        raise ValueError("Incomplete population")
    pairs = {"same_target": [], "other_target_control": []}
    for scene, rows in scenes.items():
        for first, second in combinations(rows, 2):
            if first["ann_id"] == second["ann_id"]:
                continue
            same = tuple(sorted(first["target_instances"])) == tuple(sorted(second["target_instances"]))
            record = {
                "scene": scene,
                "indices": [first["manifest_index"], second["manifest_index"]],
                "ann_ids": [first["ann_id"], second["ann_id"]],
                "same_target": same,
                "selected_iou": [first["ious"][first["selected_query"]],
                                 second["ious"][second["selected_query"]]],
                "max_iou": [max(first["ious"]), max(second["ious"])],
            }
            record["selected_discordant"] = ((record["selected_iou"][0] > .5)
                                             != (record["selected_iou"][1] > .5))
            record["adequacy_discordant"] = ((record["max_iou"][0] > .5)
                                             != (record["max_iou"][1] > .5))
            pairs["same_target" if same else "other_target_control"].append(record)
    return {
        "contract": "m95_same_target_discordance_v1",
        "capture_sha256": CAPTURE_SHA,
        "admission": False,
        "summary": {
            name: {
                "pairs": len(rows), "scenes": len({r["scene"] for r in rows}),
                "selected_discordant": sum(r["selected_discordant"] for r in rows),
                "adequacy_discordant": sum(r["adequacy_discordant"] for r in rows),
                "both_adequate_selected_discordant": sum(
                    r["selected_discordant"] and min(r["max_iou"]) > .5
                    for r in rows),
            }
            for name, rows in pairs.items()
        },
        "pairs": pairs,
        "limits": "Frozen TRAIN retrospective target identity; not native causal control, inference-time mechanism or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or sha(args.capture) != CAPTURE_SHA:
        raise ValueError("Output exists or capture differs")
    report = analyze(json.loads(args.capture.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    main()
