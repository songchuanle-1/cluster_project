"""Join existing instance names, never infer grounded anchor identity from names."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path

root = Path("/data3/songcl/Project/Cluster_project/pipeline")
capture_path = root / "anchor_identity_20260916/result.json"
annotation_path = Path("/data3/songcl/data/data_cluster/scanrefer/ScanRefer_train_new.json")
graph_path = Path("/data3/songcl/data/data_cluster/scanrefer/scene_graphs_new_train.json")
capture = json.loads(capture_path.read_text())
annotations = json.loads(annotation_path.read_text())
graphs = json.loads(graph_path.read_text())
names = defaultdict(set)
for annotation in annotations:
    names[(annotation["scene_id"], int(annotation["object_id"]))].add(
        annotation["object_name"].replace("_", " ").lower())
rows = []
for batch in capture["batches"].values():
    for i, before in enumerate(batch["base"]["rows"]):
        after = batch["anchor"]["rows"][i]
        assert (before["scene"], before["ann_id"]) == (after["scene"], after["ann_id"])
        graph = graphs[before["scene"]][str(before["ann_id"])]
        other_names = {n["target"].lower() for n in graph["graph_node"]
                       if n["node_id"] != 0 and n["node_type"] == "Object"}
        winner = before["selected_instance_overlaps"][0]
        winner_names = sorted(names[(before["scene"], winner["instance_id"])])
        targets = sorted({name for obj in before["object_ids"]
                          for name in names[(before["scene"], obj)]})
        rows.append(dict(scene=before["scene"], ann_id=before["ann_id"],
            target_ids=before["object_ids"], target_names=targets,
            winner_id=winner["instance_id"], winner_overlap=winner["iou"],
            winner_names=winner_names, winner_name_missing=not winner_names,
            winner_name_ambiguous=len(winner_names) > 1,
            before=before["layers"][-1]["selected"],
            after=after["layers"][-1]["selected"],
            winner_is_target=winner["instance_id"] in before["object_ids"],
            winner_same_name=bool(set(winner_names) & set(targets)),
            winner_matches_other_name=bool(set(winner_names) & other_names),
            other_names=sorted(other_names), utterance=graph["utterance"]))
fail = [r for r in rows if r["before"] <= .5]
confident_wrong = [r for r in fail if r["winner_overlap"] > .5 and not r["winner_is_target"]]
summary = dict(expressions=len(rows), failures=len(fail), confident_wrong=len(confident_wrong),
    missing_wrong_names=sum(r["winner_name_missing"] for r in confident_wrong),
    same_name_wrong=sum(r["winner_same_name"] for r in confident_wrong),
    lexical_other_match_wrong=sum(r["winner_matches_other_name"] for r in confident_wrong))
report = dict(summary=summary, rows=rows,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), capture_path, annotation_path, graph_path)},
    scope="FixedTRAIN123 same-forward SP mask-instance overlap;names from existing annotations. "
          "Exact lexical auxiliary-name match is not grounded anchor identity;no lemmatization "
          "or missing-name inference. Other objects may share the name.")
(root / "anchor_identity_20260916/instance_names.json").write_text(json.dumps(report, indent=2))
print(json.dumps(summary))
print(json.dumps([r for r in rows if r["scene"] == "scene0220_00" and r["ann_id"] == 21]))
