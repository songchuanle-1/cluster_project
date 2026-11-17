"""Physical all-instance nearest-neighbor control for group cues."""
import argparse
import json
from pathlib import Path

from m95_group_holdout_20260926 import digest

LOWER_SHA = "ecf6d9fe21f254e512b4fc490bc8a843a256a0a8c9e8ae5cab79c86bbf894edc"
UPPER_SHA = "e86746aac35cae5e3a47e6cf277bdc67fbd4dc14efb4ddc9811f68d499bbbe85"
GRAPH_SHA = "4cd1e5e9e3739fbaa892c91c9fd786a292a72d68b381d4898e14470fbd9c1031"
LOCAL_SHA = "d29e4cd8cb85ef37681738e8cf9c4ea24ee91ef255e1e50e9a97c31e9cdb4e8d"


def nearest(center, centers, target):
    import numpy as np

    others = [(float(np.linalg.norm((pos - center)[:2])), int(i), pos)
              for i, pos in centers.items() if int(i) != int(target)]
    if not others:
        return None
    return min(others, key=lambda row: (row[0], row[1]))


def analyze(lower, upper, graph, local, root):
    import numpy as np
    import torch

    bound = {(r["cohort"], r["scene"], int(r["ann_id"]), str(r["target"])): r
             for r in graph["rows"]}
    local_rows = {(r["cohort"], r["scene"], int(r["ann_id"]), str(r["target"])): r
                  for r in local["rows"]}
    scenes = {}
    rows = []
    for kind, document in (("lower", lower), ("upper", upper)):
        for item in document["rows"]:
            k = kind, item["scene"], int(item["ann_id"]), str(item["target"])
            if k not in bound:
                raise ValueError("Graph identity mismatch")
            if not bound[k]["target_modifier_cue"] or not item["same_name_peer_count"]:
                continue
            if k not in local_rows:
                raise ValueError("Local comparator identity mismatch")
            scene = item["scene"]
            if scene not in scenes:
                path = root / "scannetv2" / "train" / (scene + "_refer.pth")
                if digest(path) != item["scene_sha256"]:
                    raise ValueError("Scene changed: " + scene)
                xyz, _, _, _, labels = torch.load(path, map_location="cpu",
                                                  weights_only=False)
                xyz = np.asarray(xyz)[:, :3]
                labels = np.asarray(labels).astype(int)
                scene_centers = {
                    int(i): xyz[labels == i].mean(axis=0)
                    for i in np.unique(labels) if int(i) >= 0
                }
                scenes[scene] = scene_centers
            centers = scenes[scene]
            target = int(item["target"])
            if target not in centers:
                raise ValueError("Target physical instance missing")
            near = nearest(centers[target], centers, target)
            if near is None:
                raise ValueError("No other physical instance in scene")
            expected = centers[target][2] < near[2][2] if kind == "lower" else (
                centers[target][2] > near[2][2])
            reverse = centers[target][2] > near[2][2] if kind == "lower" else (
                centers[target][2] < near[2][2])
            rows.append({"cohort": kind, "scene": scene, "ann_id": item["ann_id"],
                         "target": item["target"], "all_nearest_peer": near[1],
                         "all_nearest_distance": near[0], "all_nearest_cue": bool(expected),
                         "reverse_cue": bool(reverse),
                         "same_name_nearest_cue": local_rows[k]["nearest"],
                         "same_name_peer_count": item["same_name_peer_count"]})
    unique = {}
    for row in rows:
        k = row["cohort"], row["scene"], row["target"]
        if k in unique and any(row[field] != unique[k][field]
                               for field in ("all_nearest_peer", "all_nearest_cue",
                                             "same_name_nearest_cue")):
            raise ValueError("Repeated expression physics differ")
        unique[k] = row
    summary = {}
    for kind in ("lower", "upper"):
        subset = [row for row in unique.values() if row["cohort"] == kind]
        summary[kind] = {"unique_scene_targets": len(subset),
                         "all_instance_nearest_cue": sum(row["all_nearest_cue"]
                                                         for row in subset),
                         "reverse_cue": sum(row["reverse_cue"] for row in subset),
                         "same_name_nearest_cue": sum(row["same_name_nearest_cue"]
                                                      for row in subset),
                         "peer_agreement": sum(
                             row["all_nearest_cue"] == row["same_name_nearest_cue"]
                             for row in subset)}
    return {"rows": rows, "summary": summary}


def main():
    p = argparse.ArgumentParser()
    for name in ("lower", "upper", "graph", "local", "data-root", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    for path, expected in ((a.lower, LOWER_SHA), (a.upper, UPPER_SHA),
                           (a.graph, GRAPH_SHA), (a.local, LOCAL_SHA)):
        if digest(path) != expected:
            raise ValueError("Frozen input differs: " + str(path))
    result = analyze(
        json.loads(a.lower.read_text(encoding="utf-8")),
        json.loads(a.upper.read_text(encoding="utf-8")),
        json.loads(a.graph.read_text(encoding="utf-8")),
        json.loads(a.local.read_text(encoding="utf-8")),
        a.data_root)
    result.update({"contract": "m95_group_all_instance_v1", "admission": False,
                   "lower_sha256": LOWER_SHA, "upper_sha256": UPPER_SHA,
                   "graph_sha256": GRAPH_SHA, "local_sha256": LOCAL_SHA})
    a.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                        encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
