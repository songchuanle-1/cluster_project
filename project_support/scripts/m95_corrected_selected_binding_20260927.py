"""Audit selected-query seed containment with the frozen native FPS binding."""
import argparse
import hashlib
import json
from pathlib import Path

CAPTURE_SHA = "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or sha(args.capture) != CAPTURE_SHA:
        raise ValueError("Frozen capture changed or output exists")

    import torch
    capture = json.loads(args.capture.read_text(encoding="utf-8"))
    rows = {int(row["manifest_index"]): row for row in capture["rows"]}
    if len(rows) != 256:
        raise ValueError("Incomplete frozen expression population")
    counts = {
        "positive_selected": 0, "positive_contained": 0,
        "negative_selected": 0, "negative_contained": 0,
        "bound_selected": 0, "missing_binding": 0,
    }
    seen = set()
    for entry in capture["feature_artifacts"]:
        source = args.directory / entry["path"]
        if sha(source) != entry["sha256"]:
            raise ValueError("Feature artifact hash differs")
        for artifact in torch.load(source, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            if index in seen:
                raise ValueError("Duplicate expression")
            seen.add(index)
            row = rows[index]
            query = int(row["selected_query"])
            seed = int(row["sampled_seed_indices"][query])
            superpoint = int(row["fps_superpoints"][seed])
            bound = artifact.get("identity_query", {}).get("sampled_superpoint_ids")
            if bound is None:
                counts["missing_binding"] += 1
                continue
            if int(bound[query]) != superpoint:
                raise ValueError("Captured native binding differs")
            mask = artifact["query_masks"][query]
            if not 0 <= superpoint < len(mask):
                raise ValueError("Seed outside mask axis")
            counts["bound_selected"] += 1
            category = "positive" if bool(row["native_positive"][query]) else "negative"
            counts[category + "_selected"] += 1
            counts[category + "_contained"] += int(bool(mask[superpoint]))
    if seen != set(range(256)) or counts["bound_selected"] != 256:
        raise ValueError("Frozen selected-query coverage incomplete")

    result = {
        "contract": "m95_corrected_selected_binding_v1",
        "admission": False,
        "capture_sha256": CAPTURE_SHA,
        "counts": counts,
        "positive_containment_fraction": (
            counts["positive_contained"] / counts["positive_selected"]),
        "negative_containment_fraction": (
            counts["negative_contained"] / counts["negative_selected"]),
        "limits": "Observational seed/mask containment, not identity causality or efficacy.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
