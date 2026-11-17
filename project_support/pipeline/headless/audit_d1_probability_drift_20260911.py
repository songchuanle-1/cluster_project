"""Measure CPU/GPU sigmoid drift without changing or accepting inference artifacts."""
import argparse
import json
import os
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""
import torch
from d1_candidate_bank_20260911 import sha

p = argparse.ArgumentParser()
p.add_argument("--root", required=True)
root = Path(p.parse_args().root)
torch.set_num_threads(1)
result = dict(models={}, cuda_initialized=False)
for name in ("baseline", "m95"):
    summary = json.loads((root / name / "summary.json").read_text())
    rows = []
    for row in summary["rows"]:
        path = root / name / row["artifact"]
        assert sha(path) == row["artifact_sha256"]
        bank = torch.load(path, map_location="cpu", weights_only=False)
        a = bank["mask_logits"][row["selected_index"]][bank["superpoints"]].sigmoid()
        b = bank["selected_probabilities"]
        rows.append(dict(identity=bank["identity"], max_abs=float((a - b).abs().max()),
                         absolute_1e7_pass=torch.allclose(a, b, atol=1e-7, rtol=0),
                         established_pilot_tolerance_pass=torch.allclose(a, b, atol=1e-7, rtol=1e-6),
                         binary_changes=int(((a >= .5) != (b >= .5)).sum())))
    result["models"][name] = dict(
        n=len(rows), max_abs=max(r["max_abs"] for r in rows),
        absolute_only_failures=sum(not r["absolute_1e7_pass"] for r in rows),
        established_pilot_tolerance_failures=sum(not r["established_pilot_tolerance_pass"] for r in rows),
        binary_changes=sum(r["binary_changes"] for r in rows), rows=rows)
assert not torch.cuda.is_initialized()
(root / "probability_drift_audit.json").write_text(json.dumps(result, indent=2))
print(json.dumps({k: {f: v for f, v in x.items() if f != "rows"}
                  for k, x in result["models"].items()}, indent=2))
