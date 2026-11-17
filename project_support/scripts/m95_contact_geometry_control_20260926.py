"""Native scene instance-contact geometry control for four frozen rows."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


ANCHOR_SHA = "3b6fec07b3f578ac4a828796af613f945c6751b23c37510c285b10805a57c81b"
MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sample(points):
    if not len(points):
        raise ValueError("Empty native instance")
    return points[np.linspace(0, len(points) - 1, min(len(points), 2048), dtype=int)]


def metrics(xyz, labels, candidate, anchor, relation):
    left = sample(xyz[labels == candidate])
    right = sample(xyz[labels == anchor])
    distance = float(cKDTree(right).query(left, k=1)[0].min())
    sign = None
    if "under" in relation or "below" in relation:
        sign = float(right[:, 2].mean() - left[:, 2].mean())
    elif "top" in relation:
        sign = float(left[:, 2].mean() - right[:, 2].mean())
    return {"distance": distance, "vertical_direction": sign}


def analyze(audit, manifest, data_root):
    import torch

    by_index = {int(r["manifest_index"]): r for r in manifest["rows"]}
    rows = []
    for item in audit["rows"]:
        if not item["has_unique_anchor"]:
            continue
        entry = by_index[int(item["manifest_index"])]
        scene = entry["scene_id"]
        path = data_root / "scannetv2" / "train" / (scene + "_refer.pth")
        xyz, _, _, _, labels = torch.load(path, map_location="cpu", weights_only=False)
        xyz, labels = np.asarray(xyz), np.asarray(labels).astype(int)
        target = int(entry["target_object_id"])
        peers = sorted({int(x) for x in entry["same_class_peer_object_ids"]} - {target})
        if not peers or not np.any(labels == target):
            raise ValueError("Missing native target or peer")
        edge = next(e for e in item["contact_edges"] if e["match_count"] == 1)
        anchor = int(edge["object_ids"][0])
        if anchor == target or not np.any(labels == anchor):
            raise ValueError("Anchor equals target or missing from native labels")
        controls = sorted(set(labels) - {-1, target, anchor, *peers})
        if not controls:
            raise ValueError("No shuffled-anchor control available")
        shuffled = int(controls[0])
        candidates = [target, *peers]
        observed = {str(c): metrics(xyz, labels, c, anchor, edge["relation"])
                    for c in candidates}
        negative = {str(c): metrics(xyz, labels, c, shuffled, edge["relation"])
                    for c in candidates}
        def target_wins(values):
            target_distance = values[str(target)]["distance"]
            sign = values[str(target)]["vertical_direction"]
            return (target_distance < min(values[str(c)]["distance"] for c in peers)
                    and (sign is None or sign > 0))
        rows.append({
            "manifest_index": int(item["manifest_index"]),
            "scene": scene, "failed": item["failed"],
            "target": target, "peers": peers, "anchor": anchor,
            "shuffled_anchor": shuffled, "relation": edge["relation"],
            "observed": observed, "negative_control": negative,
            "observed_target_wins": target_wins(observed),
            "negative_target_wins": target_wins(negative),
            "scene_sha256": digest(path),
        })
    if len(rows) != 4:
        raise ValueError("Anchor-resolvable cohort changed")
    return {"rows": rows,
            "failed_observed_wins": sum(r["failed"] and r["observed_target_wins"] for r in rows),
            "failed_negative_wins": sum(r["failed"] and r["negative_target_wins"] for r in rows)}


def main():
    p = argparse.ArgumentParser()
    for name in ("audit", "manifest", "data-root", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    if digest(a.audit) != ANCHOR_SHA or digest(a.manifest) != MANIFEST_SHA:
        raise ValueError("Frozen input hash differs")
    audit = json.loads(a.audit.read_text(encoding="utf-8"))
    manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
    result = analyze(audit, manifest, a.data_root)
    result.update({"contract": "m95_contact_geometry_control_v1",
                   "anchor_sha256": ANCHOR_SHA, "manifest_sha256": MANIFEST_SHA,
                   "admission": False})
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps({k: result[k] for k in ("failed_observed_wins", "failed_negative_wins")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
