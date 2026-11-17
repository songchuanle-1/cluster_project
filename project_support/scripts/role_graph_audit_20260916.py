"""Existing parser-role incidence, lexical equality is NOT coreference."""
import hashlib
import json
from pathlib import Path

root = Path("/data3/songcl/Project/Cluster_project/pipeline")
identity_path = root / "anchor_identity_20260916/result.json"
capture = json.loads(identity_path.read_text())
graph_path = Path("/data3/songcl/data/data_cluster/scanrefer/scene_graphs_new_train.json")
graphs = json.loads(graph_path.read_text())
rows = []
for batch in capture["batches"].values():
    for row in batch["base"]["rows"]:
        graph = graphs[row["scene"]][str(row["ann_id"])]
        rows.append(dict(scene=row["scene"], ann_id=row["ann_id"],
                         object_ids=row["object_ids"],
                         selected_iou=row["layers"][-1]["selected"],
                         oracle_iou=row["layers"][-1]["best"],
                         selected_instance_overlaps=row["selected_instance_overlaps"],
                         graph=graph))
report = dict(rows=rows, count=len(rows),
              sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (identity_path, graph_path, Path(__file__))},
              scope="Fixed TRAIN123 existing parse graphs;lexical overlap not coreference. "
                    "No generated annotations,model training or novelty admission.")
(root / "anchor_identity_20260916/role_graphs.json").write_text(json.dumps(report, indent=2))
for row in rows:
    if row["scene"] == "scene0220_00" and row["ann_id"] == 21:
        print(json.dumps(row, indent=2))
