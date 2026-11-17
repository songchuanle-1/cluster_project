"""Freeze an outcome-blind independent TRAIN group-cue cohort."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
SOURCE_SHA = "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
GROUP = frozenset("stack stacked row group pair column".split())
CUE = frozenset("bottom lower".split())


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def key(item):
    return (item["scene_id"], int(item["ann_id"]), str(item["object_id"]))


def selection(source, manifest):
    frozen = {(r["scene_id"], int(r["ann_id"]), str(r["target_object_id"]))
              for r in manifest["rows"]}
    if len(frozen) != 256:
        raise ValueError("Frozen identity collision")
    candidate_keys = defaultdict(list)
    for item in source:
        tokens = set(re.findall(r"[a-z]+", item["description"].lower()))
        if tokens & GROUP and tokens & CUE and key(item) not in frozen:
            candidate_keys[key(item)].append(item)
    if any(len(items) != 1 for items in candidate_keys.values()):
        raise ValueError("Duplicate selected description identity")
    rows = []
    for identity, (item,) in sorted(candidate_keys.items()):
        rows.append({"scene": identity[0], "ann_id": identity[1],
                     "target": identity[2], "object_name": item["object_name"],
                     "description": item["description"]})
    return rows


def physical(rows, source, data_root):
    import numpy as np
    import torch

    by_scene_name = defaultdict(set)
    for item in source:
        by_scene_name[(item["scene_id"], " ".join(item["object_name"].lower().split()))].add(
            str(item["object_id"]))
    scenes = {}
    results = []
    for row in rows:
        scene = row["scene"]
        if scene not in scenes:
            path = data_root / "scannetv2" / "train" / (scene + "_refer.pth")
            xyz, _, _, _, labels = torch.load(path, map_location="cpu", weights_only=False)
            scenes[scene] = (np.asarray(xyz)[:, :3], np.asarray(labels).astype(int),
                             digest(path))
        xyz, labels, scene_hash = scenes[scene]
        same_name = sorted(by_scene_name[
            (scene, " ".join(row["object_name"].lower().split()))], key=int)
        target = int(row["target"])
        if target not in set(labels.tolist()):
            raise ValueError("Missing target physical instance")
        peers = [int(i) for i in same_name if int(i) != target]
        if any(peer not in set(labels.tolist()) for peer in peers):
            raise ValueError("Missing peer physical instance")
        center = xyz[labels == target].mean(axis=0)
        ranked = sorted(
            ((float(np.linalg.norm((xyz[labels == peer].mean(axis=0) - center)[:2])),
              peer, xyz[labels == peer].mean(axis=0))
             for peer in peers), key=lambda p: (p[0], p[1]))
        if ranked:
            distance, nearest, peer_center = ranked[0]
            lower = bool(center[2] < peer_center[2])
            reversed_control = bool(center[2] > peer_center[2])
        else:
            distance = nearest = lower = reversed_control = None
        results.append({**row, "same_name_peer_count": len(peers),
                        "nearest_peer": nearest, "horizontal_distance": distance,
                        "target_below_peer": lower, "reverse_z_control": reversed_control,
                        "scene_sha256": scene_hash})
    return results


def main():
    p = argparse.ArgumentParser()
    for name in ("manifest", "source", "data-root", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    if digest(a.manifest) != MANIFEST_SHA or digest(a.source) != SOURCE_SHA:
        raise ValueError("Frozen input hash differs")
    source = json.loads(a.source.read_text(encoding="utf-8"))
    rows = selection(source, json.loads(a.manifest.read_text(encoding="utf-8")))
    result = {"contract": "m95_group_holdout_v1", "admission": False,
              "source_sha256": SOURCE_SHA, "manifest_sha256": MANIFEST_SHA,
              "rows": physical(rows, source, a.data_root)}
    result["summary"] = {
        "selected": len(rows),
        "scenes": len({r["scene"] for r in rows}),
        "resolvable": sum(r["target_below_peer"] is not None for r in result["rows"]),
        "target_lower": sum(r["target_below_peer"] is True for r in result["rows"]),
        "reverse_lower": sum(r["reverse_z_control"] is True for r in result["rows"]),
    }
    a.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
