"""Existing raw TRAIN instance features; descriptive evidence, no classifier."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import numpy as np
import torch

root = Path("/data3/songcl/Project/Cluster_project/pipeline")
data_root = Path("/data3/songcl/data/data_cluster")
source = root / "anchor_identity_20260916/instance_names.json"
records = json.loads(source.read_text())["rows"]
by_scene = defaultdict(list)
for r in records:
    by_scene[r["scene"]].append(r)
rows, hashes = [], {}
torch.set_num_threads(1)
for scene, items in by_scene.items():
    raw_path = data_root / "scannetv2/train" / (scene + "_refer.pth")
    clip_path = data_root / "clip_feat" / (scene + ".pth")
    xyz, rgb, sp, semantic, instance = torch.load(raw_path, weights_only=False, map_location="cpu")
    xyz, rgb, sp, instance = map(np.asarray, (xyz, rgb, sp, instance))
    clip = torch.load(clip_path, weights_only=False, map_location="cpu")
    if not torch.is_tensor(clip):
        raise TypeError("Expected native CLIP superpoint tensor")
    labels = {}
    for s in np.unique(sp):
        ids, counts = np.unique(instance[sp == s], return_counts=True)
        j = int(counts.argmax())
        if counts[j] > counts.sum() / 2:
            labels[int(s)] = int(ids[j])
    objects = {}
    for identity in np.unique(instance):
        if identity < 0:
            continue
        mask = instance == identity
        sps = [s for s, i in labels.items() if i == identity]
        feature = clip[sps].float().mean(0) if sps else None
        objects[int(identity)] = dict(
            centroid=xyz[mask].mean(0).tolist(), extent=np.ptp(xyz[mask], axis=0).tolist(),
            rgb_mean=rgb[mask].mean(0).tolist(),
            rgb_median=np.median(rgb[mask], axis=0).tolist(),
            points=int(mask.sum()), superpoints=len(sps), feature=feature)
    for r in items:
        if len(r["target_ids"]) != 1:
            continue
        target, winner = r["target_ids"][0], r["winner_id"]
        if target not in objects or winner not in objects:
            rows.append(dict(scene=scene, ann_id=r["ann_id"], missing=True))
            continue
        a, b = objects[target], objects[winner]
        cosines = []
        for other, obj in objects.items():
            if other == target or a["feature"] is None or obj["feature"] is None:
                continue
            cosine = float(torch.nn.functional.cosine_similarity(
                a["feature"].flatten(), obj["feature"].flatten(), dim=0))
            cosines.append((other, cosine))
        cosines.sort(key=lambda p: (-p[1], p[0]))
        rows.append(dict(scene=scene, ann_id=r["ann_id"], missing=False,
            target=target, winner=winner, before=r["before"],
            winner_overlap=r["winner_overlap"], same_name=r["winner_same_name"],
            utterance=r["utterance"],
            target_features={k: v for k, v in a.items() if k != "feature"},
            winner_features={k: v for k, v in b.items() if k != "feature"},
            target_winner_clip_cosine=next((v for i, v in cosines if i == winner), None),
            winner_clip_rank=next((j+1 for j, (i, _) in enumerate(cosines) if i == winner), None),
            other_instances=len(cosines), nearest_clip=cosines[:5]))
    hashes[scene] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (raw_path, clip_path)}
    print(json.dumps(dict(scene=scene, rows=len(rows))), flush=True)
report = dict(rows=rows, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    scene_sources=hashes,
    scope="Raw existing TRAIN geometry/RGB/native cached2D features. SP majority>0.5 "
          "as dataset;uniform SP mean descriptive only. No color thresholds,grounded "
          "relation truth,learned reranker or mechanism efficacy. Not augmented outputs.")
out = root / "instance_feature_audit_20260916"
out.mkdir(parents=True, exist_ok=True)
(out / "result.json").write_text(json.dumps(report, indent=2))
