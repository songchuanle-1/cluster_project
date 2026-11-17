"""Bounded read-only check of the three flagged nearest-query ambiguities."""
import json
import os
from pathlib import Path
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import numpy as np
import torch
from torch_scatter import scatter_mean
from d1_assignment_20260911 import sha, key

torch.set_num_threads(1)
root = Path("/tmp/cluster_d1_assignment_20260911_1113")
a = json.loads((root / "result/assignment.json").read_text())
banks = Path("/tmp/cluster_d1_expansion_20260911_0715")
rows = []
for r in a["rows"]:
    if r["nearest_float64_agrees"]:
        continue
    bankfile = banks / r["model"] / ("_".join(key(r)) + ".pth")
    assert sha(bankfile) == r["bank_sha256"]
    b = torch.load(bankfile, map_location="cpu", weights_only=False)
    raw = Path("/home/songcl/data/data/scannetv2/val") / (r["scene_id"] + "_refer.pth")
    assert sha(raw) == next(s["raw_sha256"] for s in a["scenes"] if s["scene_id"] == r["scene_id"])
    xyz, _, sp, _, ins = torch.load(raw, map_location="cpu", weights_only=False)
    _, mapping = np.unique(sp, return_inverse=True)
    counts = np.bincount(mapping)
    votes = np.bincount(mapping[ins == int(r["object_id"])], minlength=len(counts))
    mask = torch.tensor(2 * votes > counts)
    outputs = []
    for dtype in (torch.float32, torch.float64):
        centers = scatter_mean(torch.tensor(xyz, dtype=dtype), torch.tensor(mapping), dim=0)
        mu = scatter_mean(centers, mask.long(), dim=0)[1]
        distance = torch.linalg.vector_norm(centers[b["seed_indices"].long()[b["sample_indices"].long()]] - mu, dim=1)
        q = int(distance.argmin())
        positive = {i for i, v in enumerate(r["query_instance_labels"]) if v == int(r["object_id"])}
        positive.add(q)
        good = {i for i, v in enumerate(b["metrics"]["candidate_ious"]) if v > .5}
        outputs.append(dict(dtype=str(dtype), nearest=q, positive_indices=sorted(positive),
                            ties=int((distance == distance.min()).sum()),
                            positive_usable=len(positive & good),
                            labels_unchanged=positive == set(r["positive_indices"])))
    rows.append(dict(model=r["model"], scene_id=r["scene_id"], object_id=r["object_id"],
                     ann_id=r["ann_id"], source_nearest=r["nearest"], checks=outputs))
assert len(rows) == 3 and not torch.cuda.is_initialized()
print(json.dumps(dict(status="complete", rows=rows, cuda_initialized=False,
                      limit="Alternative arithmetic sensitivity, not historical GPU assignment reconstruction."), indent=2))
