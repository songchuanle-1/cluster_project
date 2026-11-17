"""Fixed TRAIN oracle comparison; no anchor choice, model or optimization."""
import hashlib
import json
from pathlib import Path

import numpy as np
import torch


def main():
    root = Path("/data3/songcl/Project/Cluster_project")
    pipeline = root / "pipeline"
    binding_path = pipeline / "entity_binding_20260916/result.json"
    vertical_path = pipeline / "vertical_relation_bounds_20260916/result.json"
    binding = {(r["scene"], r["ann_id"]): r
               for r in json.loads(binding_path.read_text())["rows"]}
    vertical = json.loads(vertical_path.read_text())["rows"]
    data = Path("/data3/songcl/data/data_cluster/scannetv2/train")
    cache, sources, rows = {}, {}, []
    torch.set_num_threads(1)
    for record in vertical:
        scene = record["scene"]
        if scene not in cache:
            path = data / (scene + "_refer.pth")
            xyz, _, _, _, labels = torch.load(path, map_location="cpu",
                                             weights_only=False)
            xyz, labels = np.asarray(xyz), np.asarray(labels)
            aggregation = data / (scene + ".aggregation.json")
            names = {int(g["id"]): g["label"] for g in
                     json.loads(aggregation.read_text())["segGroups"]}
            objects = {int(i): np.sort(xyz[labels == i, 2].astype(np.float64))
                       for i in np.unique(labels) if i >= 0}
            cache[scene] = objects, names
            for source in (path, aggregation):
                sources[str(source)] = hashlib.sha256(source.read_bytes()).hexdigest()
        objects, names = cache[scene]
        identity = binding[(scene, record["ann_id"])]
        target, winner = identity["target"], identity["winner"]
        sign = (1 if record["relation"] == "above" else -1)
        sign *= 1 if record["target_first"] else -1
        anchors = [i for i in objects if i != target and
                   names.get(i) == record["anchor_name"]]
        comparisons = []
        for anchor in anchors:
            ref = objects[anchor]
            scores = {}
            for role, instance in (("target", target), ("winner", winner)):
                if instance not in objects:
                    scores[role] = None
                    continue
                z = objects[instance]
                # Count strictly ordered point pairs without a quadratic array.
                if sign == 1:
                    count = np.searchsorted(ref, z, side="left")
                else:
                    count = len(ref) - np.searchsorted(ref, z, side="right")
                scores[role] = dict(instance=instance, same_as_anchor=instance == anchor,
                    signed_centroid=float(sign * (z.mean()-ref.mean())),
                    ordered_probability=float(count.sum(dtype=np.float64) /
                                              (len(z)*len(ref))))
            comparisons.append(dict(anchor=anchor, **scores))
        rows.append(dict(scene=scene, ann_id=record["ann_id"],
                         confident_wrong=record["confident_wrong"],
                         success=record["success"], target=target, winner=winner,
                         anchor_name=record["anchor_name"], comparisons=comparisons))
    usable = [(r, c) for r in rows for c in r["comparisons"]
              if c["target"] is not None and c["winner"] is not None
              and r["target"] != r["winner"]
              and not c["winner"]["same_as_anchor"]]
    contrasts = [dict(scene=r["scene"], ann_id=r["ann_id"], anchor=c["anchor"],
                     centroid_margin=c["target"]["signed_centroid"]-
                                     c["winner"]["signed_centroid"],
                     distribution_margin=c["target"]["ordered_probability"]-
                                         c["winner"]["ordered_probability"])
                 for r, c in usable]
    result = dict(rows=rows, contrasts=contrasts,
        summary=dict(edges=len(rows), missing_anchor=sum(not r["comparisons"] for r in rows),
                     distinct_target_winner_valid_anchor_pairs=len(contrasts),
                     distribution_only_positive=sum(c["distribution_margin"] > 0 and
                         c["centroid_margin"] <= 0 for c in contrasts),
                     centroid_only_positive=sum(c["centroid_margin"] > 0 and
                         c["distribution_margin"] <= 0 for c in contrasts)),
        scope="Fixed existing11TRAINedges;raw instance GT is oracle diagnosis only. "
              "Exact noun candidates are not identified anchors;all retained. "
              "Point-density weighting differs from native superpoint weighting. "
              "No semantic truth,deployable efficacy or statistical power claim.",
        sources=sources)
    for source in (binding_path, vertical_path, Path(__file__)):
        result["sources"][str(source)] = hashlib.sha256(source.read_bytes()).hexdigest()
    out = pipeline / "distribution_vs_centroid_20260916"
    out.mkdir(exist_ok=True)
    (out/"result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(summary=result["summary"], contrasts=contrasts), indent=2))


if __name__ == "__main__":
    main()
