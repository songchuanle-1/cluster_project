"""Verify existing raw aggregation labels against every point in fixed TRAIN scenes."""
import hashlib
import json
from pathlib import Path
import numpy as np
import torch

torch.set_num_threads(1)
root = Path("/data3/songcl/Project/Cluster_project")
data = Path("/data3/songcl/data/data_cluster/scannetv2/train")
prior_path = root/"pipeline/semantic_support_audit_20260916/result.json"
prior = json.loads(prior_path.read_text())
rows, sources, checks = [], {}, []
for scene in sorted({r["scene"] for r in prior["rows"]}):
    aggregation_path = data/(scene+".aggregation.json")
    segmentation_path = data/(scene+"_vh_clean_2.0.010000.segs.json")
    raw_path = data/(scene+"_refer.pth")
    groups = json.loads(aggregation_path.read_text())["segGroups"]
    segments = np.asarray(json.loads(segmentation_path.read_text())["segIndices"])
    native = np.asarray(torch.load(raw_path,map_location="cpu",weights_only=False)[4])
    mapping = {}
    by_id = {}
    for group in groups:
        identity = int(group["id"])
        assert identity not in by_id
        by_id[identity] = group
        for segment in group["segments"]:
            assert segment not in mapping or mapping[segment] == identity
            mapping[segment] = identity
    reconstructed = np.fromiter((mapping.get(int(s), -1) for s in segments),dtype=np.int64)
    assert reconstructed.shape == native.shape
    mismatches = int((reconstructed != native).sum())
    assert mismatches == 0, (scene,mismatches)
    checks.append(dict(scene=scene, points=len(native),mismatches=mismatches,
                       group_id_objectid_mismatches=sum(g["id"]!=g["objectId"] for g in groups)))
    for old in prior["rows"]:
        if old["scene"] != scene:
            continue
        group = by_id[old["instance"]]
        rows.append(dict(**old, raw_label=group["label"], object_id=group["objectId"]))
    for path in (aggregation_path,segmentation_path,raw_path):
        sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
ignored = [r for r in rows if r["majority_semantic"] == -100]
summary = dict(
    scenes=len(checks),points=sum(c["points"] for c in checks),point_mismatches=0,
    instances=len(rows),ignored_instances=len(ignored),
    ignored_instances_with_raw_label=sum(bool(r["raw_label"]) for r in ignored),
    raw_vocabulary=len({r["raw_label"] for r in rows}),
    ignored_raw_vocabulary=sorted({r["raw_label"] for r in ignored}),
    group_id_objectid_mismatches=sum(c["group_id_objectid_mismatches"] for c in checks))
out=root/"pipeline/raw_semantic_identity_20260916"
out.mkdir(exist_ok=True)
(out/"result.json").write_text(json.dumps(dict(
    summary=summary,rows=rows,checks=checks,scene_sources=sources,
    sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__),prior_path)},
    limitations="Existing32TRAIN raw annotations only,pointwise instance identity verified. "
    "Original raw category names are not specific utterance-anchor/coreference labels. "
    "No synonym merging,new labels,VAL/test reading or training. Vocabulary coverage "
    "does not prove label correctness or novel mechanism."
),indent=2))
print(json.dumps(summary,indent=2),flush=True)
