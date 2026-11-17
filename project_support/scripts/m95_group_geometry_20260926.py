"""Read-only scene geometry for the frozen group-word cohort."""
import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np

MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
SCREEN_SHA = "3b249386d9526296fa89df4c9b0e250a89eab388c880bcc338b0f611af2c3136"


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(data)
    return result.hexdigest()


def vertical_control(description, centers, target, peers):
    words = set(re.findall(r"[a-z]+", description.lower()))
    if not peers:
        return {"relation": "no_peers", "target_wins": None,
                "reverse_wins": None}
    z = centers[target][2]
    peer_z = [centers[p][2] for p in peers]
    if "middle" in words and "under" in words:
        return {"relation": "mixed_reference", "target_wins": None,
                "reverse_wins": None}
    if "bottom" in words or "lower" in words:
        return {"relation": "lower", "target_wins": z < min(peer_z),
                "reverse_wins": z > max(peer_z)}
    if "middle" in words:
        return {"relation": "middle", "target_wins": min(peer_z) < z < max(peer_z),
                "reverse_wins": None}
    if "under" in words:
        return {"relation": "under_reference", "target_wins": None,
                "reverse_wins": None}
    return {"relation": "no_vertical_cue", "target_wins": None,
            "reverse_wins": None}


def analyze(manifest, screen, data_root):
    import torch

    by_index = {int(row["manifest_index"]): row for row in manifest["rows"]}
    rows = []
    for exposed in screen["exposed_descriptions"]:
        index = int(exposed["manifest_index"])
        entry = by_index[index]
        scene = entry["scene_id"]
        if exposed["scene"] != scene:
            raise ValueError("Scene identity differs")
        path = data_root / "scannetv2" / "train" / (scene + "_refer.pth")
        xyz, _, _, _, physical = torch.load(
            path, map_location="cpu", weights_only=False
        )
        xyz = np.asarray(xyz)
        labels = np.asarray(physical).astype(int)
        target = int(entry["target_object_id"])
        peers = sorted({int(p) for p in entry["same_class_peer_object_ids"]}
                       - {target})
        centers, instances = {}, {}
        for object_id in [target, *peers]:
            points = xyz[labels == object_id]
            if not len(points):
                raise ValueError("Missing physical instance: " + str(object_id))
            centers[object_id] = points[:, :3].mean(axis=0).tolist()
            instances[str(object_id)] = {
                "points": len(points),
                "centroid": centers[object_id],
                "z_quantiles": np.quantile(points[:, 2], [0.1, 0.9]).tolist(),
            }
        rows.append({
            "manifest_index": index, "scene": scene, "target": target,
            "peers": peers, "failed": exposed["failed"],
            "description": exposed["description"],
            "scene_sha256": digest(path), "instances": instances,
            "vertical": vertical_control(
                exposed["description"], centers, target, peers),
        })
    if len(rows) != 7:
        raise ValueError("Frozen group cohort differs")
    return {"contract": "m95_group_geometry_v1",
            "manifest_sha256": MANIFEST_SHA, "screen_sha256": SCREEN_SHA,
            "rows": rows, "admission": False}


def main():
    p = argparse.ArgumentParser()
    for name in ("manifest", "screen", "data-root", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    if digest(args.manifest) != MANIFEST_SHA or digest(args.screen) != SCREEN_SHA:
        raise ValueError("Frozen input hash differs")
    result = analyze(
        json.loads(args.manifest.read_text(encoding="utf-8")),
        json.loads(args.screen.read_text(encoding="utf-8")),
        args.data_root,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps([{"index": r["manifest_index"], "failed": r["failed"],
                       "peers": len(r["peers"]), **r["vertical"]}
                      for r in result["rows"]], sort_keys=True))


if __name__ == "__main__":
    main()
