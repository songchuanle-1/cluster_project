"""Existing TRAIN raw-geometry bounds over all exact-name anchor candidates."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import numpy as np
import torch

ROOT = Path("/data3/songcl/Project/Cluster_project")
DATA = Path("/data3/songcl/data/data_cluster")
source = ROOT / "pipeline/entity_binding_20260916/result.json"
annotations = DATA / "scanrefer/ScanRefer_train_new.json"
names = defaultdict(set)
for a in json.loads(annotations.read_text()):
    names[(a["scene_id"], int(a["object_id"]))].add(
        a["object_name"].replace("_", " ").lower())
records = json.loads(source.read_text())["rows"]
by_scene = defaultdict(list)
for r in records:
    by_scene[r["scene"]].append(r)
torch.set_num_threads(1)
rows, hashes = [], {}
allowed = {"above": 1, "below": -1, "under": -1, "underneath": -1}
for scene, expressions in by_scene.items():
    eligible = [(r, e) for r in expressions for e in r["edges"]
                if e["relation"].lower() in allowed
                and (e["obj_idx"] == 0 or e["sub_idx"] == 0)]
    if not eligible:
        continue
    path = DATA / "scannetv2/train" / (scene + "_refer.pth")
    xyz, _, _, _, instance = torch.load(path, weights_only=False, map_location="cpu")
    xyz, instance = np.asarray(xyz), np.asarray(instance)
    objects = {}
    for obj in np.unique(instance):
        if obj < 0:
            continue
        points = xyz[instance == obj]
        objects[int(obj)] = dict(mean=points.mean(0), lo=points.min(0), hi=points.max(0))
    hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    for r, edge in eligible:
        target_first = edge["obj_idx"] == 0
        anchor_node = edge["sub_idx"] if target_first else edge["obj_idx"]
        entity = next((e for e in r["entities"] if e["node_id"] == anchor_node), None)
        if entity is None:
            rows.append(dict(scene=scene, ann_id=r["ann_id"], missing="anchor_node"))
            continue
        noun = " ".join(s["text"] for s in entity["spans"]["target_char_span"]).lower()
        anchors = [obj for obj in objects if obj != r["target"] and noun in names[(scene, obj)]]
        sign = allowed[edge["relation"].lower()] * (1 if target_first else -1)
        evaluations = []
        for anchor in anchors:
            values = {}
            for role in ("target", "winner"):
                obj = objects.get(r[role])
                if obj is None:
                    values[role] = None
                    continue
                ref = objects[anchor]
                values[role] = dict(
                    same_as_anchor=r[role] == anchor,
                    signed_center_height=float(sign * (obj["mean"][2]-ref["mean"][2])),
                    full_height_separation=float(
                        obj["lo"][2]-ref["hi"][2] if sign == 1
                        else ref["lo"][2]-obj["hi"][2]),
                )
            evaluations.append(dict(anchor=anchor, **values))
        rows.append(dict(scene=scene, ann_id=r["ann_id"], caption=r["caption"],
                         relation=edge["relation"], target_first=target_first,
                         anchor_name=noun, anchors=anchors, evaluations=evaluations,
                         success=r["success"], confident_wrong=r["confident_wrong"]))
summary = dict(edges=len(rows), expressions=len({(r["scene"], r["ann_id"]) for r in rows}),
               no_exact_anchor=sum(not r.get("anchors") for r in rows),
               unique_anchor=sum(len(r.get("anchors", [])) == 1 for r in rows),
               multiple_anchor=sum(len(r.get("anchors", [])) > 1 for r in rows),
               confident_wrong_edges=sum(r.get("confident_wrong", False) for r in rows))
out = ROOT / "pipeline/vertical_relation_bounds_20260916"
out.mkdir(exist_ok=True)
(out / "result.json").write_text(json.dumps(dict(
    summary=summary, rows=rows, scene_sources=hashes,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), source, annotations)},
    limitations="Raw z-axis geometric proxies, not semantic truth or verified "
    "gravity calibration. Strict single-token relation whitelist excludes composed "
    "relations. Names from existing ScanRefer annotations may omit anchors. No "
    "synonyms, nearest-anchor choice, outcome selection or new labels. Vertical "
    "center ordering does not establish under/above semantics; object extents overlap."
), indent=2))
print(json.dumps(summary), flush=True)
