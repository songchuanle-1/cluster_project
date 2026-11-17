"""Join the frozen valid-peer distance census to native deployed outcomes."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from m95_native_positive_union_20260927 import CAPTURE_SHA, sha

DISTANCE_SHA = "e2a555be421ebb3f8d3c17a9667092832c29796fba30db05087045ff5d1b64c5"


def analyze(distance_path, capture_path):
    if sha(distance_path) != DISTANCE_SHA or sha(capture_path) != CAPTURE_SHA:
        raise ValueError("Frozen input SHA256 differs")
    distance = json.loads(distance_path.read_text(encoding="utf-8"))
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if (distance["capture_sha256"] != CAPTURE_SHA
            or distance["contract"] != "m95_valid_peer_blind_distance_v1"
            or len(capture["rows"]) != 256):
        raise ValueError("Frozen manifest differs")
    native = {r["manifest_index"]: r for r in capture["rows"]}
    strata = defaultdict(list)
    rows = []
    for cohort, group in distance["groups"].items():
        for item in group["rows"]:
            r = native[item["manifest_index"]]
            if r["scene"] != item["scene"]:
                raise ValueError("Scene axis differs")
            selected = float(r["ious"][r["selected_query"]])
            max_iou = max(float(x) for x in r["ious"])
            row = {
                "manifest_index": item["manifest_index"], "scene": item["scene"],
                "cohort": cohort, "selected_iou": selected,
                "max_iou": max_iou, "deployed_failure": selected <= .5,
                "mask_limited": max_iou <= .5,
                "original_target_closer": item["original"]["target_closer"],
                "rolled_target_closer": item["rolled"]["target_closer"],
            }
            rows.append(row)
            strata["deployed_failure" if row["deployed_failure"] else "deployed_success"].append(row)
            strata["mask_limited" if row["mask_limited"] else "mask_capable"].append(row)
    if len(rows) != 33 or len({r["manifest_index"] for r in rows}) != 33:
        raise ValueError("Frozen cohort differs")
    result = {}
    for name, group in strata.items():
        result[name] = {
            "expressions": len(group), "scenes": len({r["scene"] for r in group}),
            "original_target_closer": sum(r["original_target_closer"] for r in group),
            "rolled_target_closer": sum(r["rolled_target_closer"] for r in group),
        }
    return {
        "contract": "m95_valid_peer_failure_link_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "distance_sha256": DISTANCE_SHA,
        "strata": result, "rows": sorted(rows, key=lambda r: r["manifest_index"]),
        "limits": "Retrospective TRAIN selection association, not a mechanism or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("distance", "capture", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.distance, args.capture)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["strata"]))


if __name__ == "__main__":
    main()
