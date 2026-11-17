"""Read-only physical control of an exploratory group-orientation cue."""
import argparse
import json
from pathlib import Path

from m95_group_holdout_20260926 import digest

LOWER_SHA = "ecf6d9fe21f254e512b4fc490bc8a843a256a0a8c9e8ae5cab79c86bbf894edc"
UPPER_SHA = "e86746aac35cae5e3a47e6cf277bdc67fbd4dc14efb4ddc9811f68d499bbbe85"
GRAPH_SHA = "4cd1e5e9e3739fbaa892c91c9fd786a292a72d68b381d4898e14470fbd9c1031"


def compare(target_z, peer_z, lower):
    values = list(peer_z)
    if not values:
        raise ValueError("At least one peer required")
    if lower:
        return target_z < min(values)
    return target_z > max(values)


def analyze(lower, upper, graph, data_root):
    import numpy as np
    import torch

    graph_rows = {
        (r["cohort"], r["scene"], int(r["ann_id"]), str(r["target"])): r
        for r in graph["rows"]
    }
    scenes = {}
    rows = []
    for cohort, doc in (("lower", lower), ("upper", upper)):
        for row in doc["rows"]:
            k = cohort, row["scene"], int(row["ann_id"]), str(row["target"])
            binding = graph_rows.get(k)
            if binding is None:
                raise ValueError("Graph cohort binding differs")
            if not binding["target_modifier_cue"] or not row["same_name_peer_count"]:
                continue
            scene = row["scene"]
            if scene not in scenes:
                path = data_root / "scannetv2" / "train" / (scene + "_refer.pth")
                if digest(path) != row["scene_sha256"]:
                    raise ValueError("Scene bytes differ: " + scene)
                xyz, _, _, _, labels = torch.load(path, map_location="cpu",
                                                  weights_only=False)
                scenes[scene] = np.asarray(xyz)[:, :3], np.asarray(labels).astype(int)
            xyz, labels = scenes[scene]
            target = int(row["target"])
            center = xyz[labels == target].mean(axis=0)
            if not np.all(np.isfinite(center)):
                raise ValueError("Target missing or nonfinite")
            candidate_ids = {
                int(peer) for peer in row.get("same_name_peers", [])
            }
            if not candidate_ids:
                # The cohorts record only the count. The complete IDs must
                # come from the same native description source in main().
                raise ValueError("Physical peer identities missing")
            peers = []
            for peer in candidate_ids:
                points = xyz[labels == peer]
                if not len(points):
                    raise ValueError("Physical peer missing")
                centroid = points.mean(axis=0)
                peers.append((float(np.linalg.norm((centroid - center)[:2])),
                              peer, float(centroid[2])))
            peers.sort(key=lambda value: (value[0], value[1]))
            z = float(center[2])
            is_lower = cohort == "lower"
            nearest = compare(z, [peers[0][2]], is_lower)
            farthest = compare(z, [peers[-1][2]], is_lower)
            global_cue = compare(z, [peer[2] for peer in peers], is_lower)
            if nearest != (row["target_below_peer"] if is_lower
                           else row["reverse_z_control"]):
                raise ValueError("Frozen nearest-peer rule differs")
            rows.append({
                "cohort": cohort, "scene": scene, "ann_id": row["ann_id"],
                "target": row["target"], "peer_count": len(peers),
                "nearest": nearest, "farthest": farthest,
                "all_peers": global_cue,
                "nearest_peer": peers[0][1], "farthest_peer": peers[-1][1],
            })
    identities = {}
    for row in rows:
        k = row["cohort"], row["scene"], row["target"]
        if k in identities and any(row[f] != identities[k][f]
                                   for f in ("nearest", "farthest", "all_peers")):
            raise ValueError("Repeated referent has conflicting physics")
        identities[k] = row
    summary = {}
    for cohort in ("lower", "upper"):
        selected = [r for r in identities.values() if r["cohort"] == cohort]
        summary[cohort] = {"unique_scene_targets": len(selected),
                           **{k: sum(r[k] for r in selected)
                              for k in ("nearest", "farthest", "all_peers")}}
    return {"rows": rows, "summary": summary}


def main():
    from collections import defaultdict

    p = argparse.ArgumentParser()
    for name in ("lower", "upper", "graph", "source", "data-root", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    for path, expected in ((a.lower, LOWER_SHA), (a.upper, UPPER_SHA),
                           (a.graph, GRAPH_SHA)):
        if digest(path) != expected:
            raise ValueError("Frozen input differs")
    source = json.loads(a.source.read_text(encoding="utf-8"))
    by_scene_name = defaultdict(set)
    for item in source:
        name = " ".join(item["object_name"].lower().split())
        by_scene_name[(item["scene_id"], name)].add(str(item["object_id"]))
    lower = json.loads(a.lower.read_text(encoding="utf-8"))
    upper = json.loads(a.upper.read_text(encoding="utf-8"))
    for doc in (lower, upper):
        for row in doc["rows"]:
            name = " ".join(row["object_name"].lower().split())
            row["same_name_peers"] = sorted(
                by_scene_name[(row["scene"], name)] - {str(row["target"])}, key=int)
            if len(row["same_name_peers"]) != row["same_name_peer_count"]:
                raise ValueError("Same-name peer registry differs")
    result = analyze(lower, upper,
                     json.loads(a.graph.read_text(encoding="utf-8")),
                     a.data_root)
    result.update({"contract": "m95_group_local_global_v1", "admission": False,
                   "lower_sha256": LOWER_SHA, "upper_sha256": UPPER_SHA,
                   "graph_sha256": GRAPH_SHA, "source_sha256": digest(a.source)})
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
