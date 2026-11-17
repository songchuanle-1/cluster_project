"""Frozen three-row native ordinal diagnosis; no model or outcome selection."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch


MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
BINDING_SHA = "3db88c9dca9f37d9ca13cb555685c90ee05801bebdc1da81fb7a720c8a4a726d"
INDICES = (7, 10, 44)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyze(manifest, binding, source, data_root):
    entries = {int(row["manifest_index"]): row for row in manifest["rows"]}
    strict = {int(row["manifest_index"]): row for row in binding["rows"]
              if row["strict_sequence"]}
    if set(strict) != set(INDICES) or any(not strict[i]["failed"] for i in INDICES):
        raise ValueError("Strict frozen cohort changed")
    object_names = defaultdict(lambda: defaultdict(set))
    for item in source:
        object_names[item["scene_id"]][item["object_name"].lower().strip()].add(
            int(item["object_id"]))
    rows = []
    for index in INDICES:
        entry = entries[index]
        scene = entry["scene_id"]
        path = data_root / "scannetv2" / "train" / (scene + "_refer.pth")
        xyz, _, _, _, labels = torch.load(path, map_location="cpu", weights_only=False)
        xyz, labels = np.asarray(xyz), np.asarray(labels, dtype=int)
        target = int(entry["target_object_id"])
        peers = sorted({int(x) for x in entry["same_class_peer_object_ids"]} - {target})
        ids = [target, *peers]
        if not peers or any(not np.any(labels == i) for i in ids):
            raise ValueError("Native target/peer support missing")
        centers = {str(i): xyz[labels == i].mean(axis=0).tolist() for i in ids}
        ranks = {}
        for axis, axis_name in enumerate(("x", "y")):
            for reverse in (False, True):
                ordered = sorted(ids, key=lambda i: (
                    -centers[str(i)][axis] if reverse else centers[str(i)][axis], i))
                ranks[axis_name + ("_descending" if reverse else "_ascending")] = {
                    "target_rank": ordered.index(target) + 1, "order": ordered}
        anchor_name = {7: "door", 10: "table", 44: None}[index]
        anchors = sorted(object_names[scene].get(anchor_name, set())) if anchor_name else []
        rows.append({
            "manifest_index": index, "scene": scene, "target": target, "peers": peers,
            "description": strict[index]["description"],
            "parser_target_modifier_bound": strict[index]["target_modifier_bound"],
            "anchor_name": anchor_name, "anchor_ids": anchors,
            "anchor_unique": len(anchors) == 1,
            "reference_frame_resolved": False,
            "centroids": centers, "axis_reversal_control": ranks,
            "scene_sha256": digest(path),
        })
    return {"contract": "m95_ordinal_native_order_v1", "manifest_sha256": MANIFEST_SHA,
            "binding_sha256": BINDING_SHA, "rows": rows, "admission": False,
            "interpretation": "World-axis ranks are descriptive only; no camera-relative frame or target-bound ordinal intervention."}


def main():
    parser = argparse.ArgumentParser()
    for field in ("manifest", "binding", "source", "data-root", "output"):
        parser.add_argument("--" + field, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output already exists")
    if digest(args.manifest) != MANIFEST_SHA or digest(args.binding) != BINDING_SHA:
        raise ValueError("Frozen inputs differ")
    result = analyze(
        json.loads(args.manifest.read_text(encoding="utf-8")),
        json.loads(args.binding.read_text(encoding="utf-8")),
        json.loads(args.source.read_text(encoding="utf-8")),
        args.data_root)
    result["source_sha256"] = digest(args.source)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps([{"index": r["manifest_index"], "anchors": len(r["anchor_ids"]),
                       "ranks": {k: v["target_rank"] for k, v in
                                 r["axis_reversal_control"].items()}}
                      for r in result["rows"]], sort_keys=True))


if __name__ == "__main__":
    main()
