"""Existing point semantic labels versus named instances; TRAIN diagnostic."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import numpy as np
import torch

torch.set_num_threads(1)
root = Path("/data3/songcl/Project/Cluster_project")
data = Path("/data3/songcl/data/data_cluster")
binding_path = root/"pipeline/entity_binding_20260916/result.json"
ann_path = data/"scanrefer/ScanRefer_train_new.json"
binding = json.loads(binding_path.read_text())["rows"]
names = defaultdict(set)
for a in json.loads(ann_path.read_text()):
    names[(a["scene_id"], int(a["object_id"]))].add(a["object_name"].replace("_"," "))
rows, sources = [], {}
for scene in sorted({r["scene"] for r in binding}):
    path = data/"scannetv2/train"/(scene+"_refer.pth")
    xyz, rgb, sp, semantic, instance = torch.load(path,map_location="cpu",weights_only=False)
    semantic, instance = np.asarray(semantic), np.asarray(instance)
    assert len(semantic) == len(instance) == len(xyz)
    sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    for identity in np.unique(instance):
        if identity < 0:
            continue
        mask = instance == identity
        counts = Counter(map(int,semantic[mask]))
        majority, count = counts.most_common(1)[0]
        rows.append(dict(scene=scene, instance=int(identity), points=int(mask.sum()),
                         names=sorted(names[(scene,int(identity))]),
                         semantic_counts=dict(counts), majority_semantic=majority,
                         majority_fraction=count/int(mask.sum())))
named = defaultdict(Counter)
for row in rows:
    for name in row["names"]:
        named[name][row["majority_semantic"]] += 1
summary = dict(scenes=len(sources), instances=len(rows),
               named_instances=sum(bool(r["names"]) for r in rows),
               pure_instances=sum(len(r["semantic_counts"])==1 for r in rows),
               semantic_ids=sorted({k for r in rows for k in r["semantic_counts"]}),
               name_to_majority_semantic={k:dict(v) for k,v in sorted(named.items())})
out=root/"pipeline/semantic_support_audit_20260916"
out.mkdir(exist_ok=True)
(out/"result.json").write_text(json.dumps(dict(
    summary=summary,rows=rows,scene_sources=sources,
    sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__),binding_path,ann_path)},
    limitations="Existing32TRAIN scenes,raw semantic integers and annotation names. "
    "No guessed class-name mapping, new labels, model supervision or inference oracle. "
    "Class availability is not referent identity; other/ignored classes may merge "
    "different nouns. Purity is within existing instances,not semantic annotation accuracy."
),indent=2))
print(json.dumps(summary,indent=2),flush=True)
