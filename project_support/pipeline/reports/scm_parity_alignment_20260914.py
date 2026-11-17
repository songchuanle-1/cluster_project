"""Diagnose raw parity failure without substituting aligned outputs for exact parity."""
import json
from pathlib import Path
import sys
import torch

work = Path(sys.argv[1])
a = torch.load(work / "parent_outputs.pth", weights_only=False)
b = torch.load(work / "scm_outputs.pth", weights_only=False)
rows = []
for i, (left, right) in enumerate(zip(a["sample_inds"], b["sample_inds"])):
    assert left.unique().numel() == left.numel()
    assert right.unique().numel() == right.numel()
    same_set = torch.equal(left.sort().values, right.sort().values)
    row = dict(expression=i, same_membership=same_set)
    if same_set:
        ia, ib = left.argsort(), right.argsort()
        for key in ("masks", "indis"):
            row[key + "_aligned_max"] = float(
                (a[key][i, ia] - b[key][i, ib]).abs().max())
        qa = a["indis"][i].softmax(-1)[:, 1].argmax()
        qb = b["indis"][i].softmax(-1)[:, 1].argmax()
        row["same_selected_seed"] = bool(left[qa] == right[qb])
        row["same_hard_mask"] = torch.equal(a["masks"][i, qa] > 0,
                                           b["masks"][i, qb] > 0)
    rows.append(row)
(work / "parity_alignment.json").write_text(json.dumps(rows, indent=2))
print(json.dumps(rows, indent=2))
