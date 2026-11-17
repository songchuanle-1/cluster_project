"""Scene-balanced summary of four sequential native diagnostic batches."""
import json
from pathlib import Path
import torch
import numpy as np

folders = ["component_free_sampling_server4_20260915",
           "component_free_sampling_extra_20260915"]
all_rows = []
for folder in folders:
    root = Path("/tmp") / folder
    report = json.loads((root / "aligned.json").read_text())
    for batch in report["results"]:
        data = torch.load(root / f"batch_{batch['batch']}_global.pth",
                          map_location="cpu", weights_only=False)
        # Current native loader groups annotations by scene. Recover group sizes
        # from the same deterministic batches, not an assumed four per scene.
        base = Path("/tmp/component_full_loss_20260915.py")
        if folder.endswith("extra_20260915"):
            base = Path("/tmp/component_full_loss_extra_20260915.py")
        # Metadata lacks scenes_len: report expression-balanced results instead
        # of fabricating scene ownership. Scene IDs remain an explicit batch set.
        for row in batch["rows"]:
            all_rows.append(dict(
                source=folder, batch=batch["batch"], scenes=data["scenes"],
                expression=row["expression"],
                ann_id=data["ann_ids"][row["expression"]],
                components=row["components"],
                delta=row["metrics"]["component"]["hard_iou"]-row["metrics"]["global"]["hard_iou"],
                noise=row["metrics"]["global_repeat"]["hard_iou"]-row["metrics"]["global"]["hard_iou"]))
summary = {}
for subset in ("all", "connected", "disconnected"):
    chosen = [r for r in all_rows if subset == "all" or
              (r["components"] == 1 if subset == "connected" else r["components"] > 1)]
    groups = {}
    for r in chosen:
        key = (r["source"], r["batch"], r["expression"])
        groups.setdefault(key, []).append(r["delta"])
    summary[subset] = dict(queries=len(chosen), expressions=len(groups),
        query_mean=float(np.mean([r["delta"] for r in chosen])) if chosen else None,
        expression_mean=float(np.mean([np.mean(v) for v in groups.values()])) if groups else None,
        positive_expressions=int(sum(np.mean(v)>0 for v in groups.values())),
        negative_expressions=int(sum(np.mean(v)<0 for v in groups.values())),
        max_abs_duplicate_noise=max((abs(r["noise"]) for r in chosen),default=0))
Path("/tmp/component_four_batch_summary_20260915.json").write_text(json.dumps(dict(
    summary=summary, rows=all_rows,
    limitation="Scene membership per expression not stored in old capture;no scene CI until recovered. Four batches,not training efficacy."),indent=2))
print(json.dumps(summary))
