"""Inspect existing annotations for all altered anchor-deletion outcomes."""
import json
from pathlib import Path

root = Path("/data3/songcl/Project/Cluster_project/pipeline")
report = json.loads((root / "anchor_access_20260916/result.json").read_text())
identities = set()
for batch in report["batches"].values():
    for before, after in zip(batch["base"]["rows"], batch["anchor"]["rows"]):
        if before["layers"][-1]["selected"] != after["layers"][-1]["selected"]:
            identities.add((before["scene"], str(before["ann_id"]),
                            tuple(str(v) for v in before["object_ids"])))
annotations = json.loads(Path(
    "/data3/songcl/data/data_cluster/scanrefer/ScanRefer_train_new.json").read_text())
rows = [r for r in annotations if any(
    r["scene_id"] == scene and str(r["ann_id"]) == ann and str(r["object_id"]) in objects
    for scene, ann, objects in identities)]
output = dict(expected_identities=len(identities), found=len(rows), rows=rows,
              scope="Post-outcome case inspection, not independent confirmation.")
(root / "anchor_access_20260916/annotations.json").write_text(json.dumps(output, indent=2))
for row in rows:
    print(json.dumps({k: row[k] for k in ("scene_id", "ann_id", "object_id", "object_name", "description") if k in row}))
