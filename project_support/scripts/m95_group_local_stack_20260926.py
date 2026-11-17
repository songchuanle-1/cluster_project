"""Outcome-blind nearest-horizontal-peer diagnostic on frozen group rows."""
import argparse
import hashlib
import json
import re
from pathlib import Path

GEOMETRY_SHA = "1eb77f4ff466877e872bc084a3e52aa2afaf31ede2d0a88e45ab5dbc48a88766"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_peer(row):
    target = row["instances"][str(row["target"])]["centroid"]
    peers = row["peers"]
    if not peers:
        return None
    return min(peers, key=lambda ident: (
        sum((a - b) ** 2 for a, b in zip(
            target[:2], row["instances"][str(ident)]["centroid"][:2])),
        ident,
    ))


def analyze(geometry):
    rows = []
    for row in geometry["rows"]:
        peer = local_peer(row)
        words = set(re.findall(r"[a-z]+", row["description"].lower()))
        cue = "bottom" in words or "lower" in words
        if peer is None:
            relation = "no_peers"
        elif "middle" in words and "under" in words:
            relation = "mixed_reference"
        elif cue:
            relation = "lower"
        elif "under" in words:
            relation = "under_reference"
        else:
            relation = "no_vertical_cue"
        target = row["instances"][str(row["target"])]["centroid"]
        other = row["instances"][str(peer)]["centroid"] if peer is not None else None
        rows.append({
            "manifest_index": row["manifest_index"], "failed": row["failed"],
            "relation": relation, "nearest_peer": peer,
            "horizontal_distance": (
                sum((a - b) ** 2 for a, b in zip(target[:2], other[:2])) ** .5
                if other is not None else None),
            "target_below_peer": (target[2] < other[2]
                                  if relation == "lower" else None),
            "reverse_z_control": (target[2] > other[2]
                                  if relation == "lower" else None),
        })
    if len(rows) != 7:
        raise ValueError("Frozen cohort differs")
    return {"contract": "m95_group_local_stack_v1",
            "geometry_sha256": GEOMETRY_SHA, "rows": rows, "admission": False,
            "scope": "Exploratory GT-bound physical diagnosis; no native model intervention"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--geometry", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    if digest(args.geometry) != GEOMETRY_SHA:
        raise ValueError("Geometry artifact differs")
    result = analyze(json.loads(args.geometry.read_text(encoding="ascii")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["rows"], sort_keys=True))


if __name__ == "__main__":
    main()
