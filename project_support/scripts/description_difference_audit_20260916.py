"""TRAIN-only supervision audit; no training or admission claim."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import numpy as np
import torch

root = Path("/data3/songcl/Project/Cluster_project/pipeline")
data = Path("/data3/songcl/data/data_cluster/scanrefer/ScanRefer_train_new.json")
inventory = root / "anchor_identity_20260916/instance_names.json"
scenes = {r["scene"] for r in json.loads(inventory.read_text())["rows"]}
records = json.loads(data.read_text())
groups = defaultdict(list)
for r in records:
    if r["scene_id"] in scenes:
        groups[r["scene_id"]].append(r)


def distance(a, b):
    a, b = set(a), set(b)
    return len(a ^ b) / max(len(a | b), 1)


rows = []
for scene, members in sorted(groups.items()):
    within, between, examples = [], [], []
    for i, a in enumerate(members):
        for b in members[i + 1:]:
            if a["object_name"] != b["object_name"]:
                continue
            d = distance(a["token"], b["token"])
            same = str(a["object_id"]) == str(b["object_id"])
            (within if same else between).append(d)
            if same and d > 0 and len(examples) < 2:
                examples.append(dict(object_id=a["object_id"],
                    ann_ids=[a["ann_id"], b["ann_id"]],
                    descriptions=[a["description"], b["description"]],
                    token_set_distance=d))
    rows.append(dict(scene=scene, descriptions=len(members),
        same_object_pairs=len(within), different_object_same_name_pairs=len(between),
        same_mean=float(np.mean(within)) if within else None,
        different_mean=float(np.mean(between)) if between else None,
        same_nonzero=sum(d > 0 for d in within), examples=examples))

# Complete ordered pair residual loss equals twice centered residual variance.
torch.set_num_threads(1)
torch.manual_seed(1999)
x = torch.randn(7, 5, dtype=torch.float64, device="cuda", requires_grad=True)
y = torch.randn_like(x)
e = x - y
pair = ((e[:, None] - e[None, :]) ** 2).sum(-1).mean()
centered = 2 * ((e - e.mean(0)) ** 2).sum(-1).mean()
g_pair = torch.autograd.grad(pair, x, retain_graph=True)[0]
g_centered = torch.autograd.grad(centered, x)[0]
assert torch.allclose(pair, centered, atol=1e-12, rtol=1e-12)
assert torch.allclose(g_pair, g_centered, atol=1e-12, rtol=1e-12)
report = dict(rows=rows, summary=dict(
    scenes=len(rows), descriptions=sum(r["descriptions"] for r in rows),
    same_object_pairs=sum(r["same_object_pairs"] for r in rows),
    same_nonzero=sum(r["same_nonzero"] for r in rows),
    different_object_same_name_pairs=sum(r["different_object_same_name_pairs"] for r in rows)),
    algebra=dict(pair_loss=float(pair.detach()), centered_loss=float(centered.detach()),
        gradient_max_error=float((g_pair-g_centered).abs().max()),
        identity_pass=True, device=torch.cuda.get_device_name()),
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), data, inventory)},
    limitations="Existing TRAIN annotations in fixed32scenes only. Token-set distance "
    "does not establish semantic contradiction or object attribute truth. Same-object "
    "variation invalidates a deterministic visual-difference-only reconstruction "
    "assumption, not all conditional language generation. Complete pairwise squared "
    "loss is centered regression; no novel graph or admission established.")
destination = root / "description_difference_20260916"
destination.mkdir(exist_ok=True)
(destination / "result.json").write_text(json.dumps(report, indent=2))
print(json.dumps(dict(summary=report["summary"], algebra=report["algebra"])), flush=True)
