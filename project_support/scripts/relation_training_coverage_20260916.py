"""TRAIN-only applicability inventory; no relation or anchor ground-truth labels."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

ROOT = Path("/data3/songcl/Project/Cluster_project")
DATA = Path("/data3/songcl/data/data_cluster/scanrefer")
annotations_path = DATA / "ScanRefer_train_new.json"
graphs_path = DATA / "scene_graphs_new_train.json"
annotations = json.loads(annotations_path.read_text())
graphs = json.loads(graphs_path.read_text())
names = defaultdict(lambda: defaultdict(set))
for annotation in annotations:
    names[annotation["scene_id"]][annotation["object_name"].replace("_", " ").lower()].add(
        int(annotation["object_id"]))
allowed = {"above": 1, "below": -1, "under": -1, "underneath": -1}
rows = []
keys = set()
missing = []
for annotation in annotations:
    scene, ann = annotation["scene_id"], str(annotation["ann_id"])
    key = (scene, ann)
    if key in keys:
        raise ValueError(f"Duplicate scene/annotation key: {key}")
    keys.add(key)
    target = int(annotation["object_id"])
    graph = graphs.get(scene, {}).get(ann)
    if graph is None:
        missing.append(dict(scene=scene, ann_id=ann))
        continue
    nodes = {n["node_id"]: n for n in graph["graph_node"]}
    edges = []
    for edge in graph["graph_edge"]:
        relation = edge["relation"].lower()
        if relation not in allowed:
            continue
        first, second = edge["obj_idx"], edge["sub_idx"]
        if (first == 0) == (second == 0):
            continue
        anchor_id = second if first == 0 else first
        node = nodes.get(anchor_id)
        if node is None or node["node_type"] != "Object":
            continue
        name = node["target"].lower()
        candidates = sorted(names[scene].get(name, set()) - {target})
        edges.append(dict(
            relation=relation, direction=allowed[relation]*(1 if first == 0 else -1),
            anchor_node=anchor_id, anchor_name=name, candidates=candidates,
            same_name_as_target=name in names[scene] and target in names[scene][name]))
    if edges:
        rows.append(dict(scene=scene, ann_id=ann, target=target,
                         caption=graph["utterance"], edges=edges))

all_edges = [edge for row in rows for edge in row["edges"]]
identified = [row for row in rows if any(e["candidates"] for e in row["edges"])]
single = [row for row in rows if len(row["edges"]) == 1 and len(row["edges"][0]["candidates"]) == 1]
scene_counts = Counter(row["scene"] for row in identified)
summary = dict(
    train_annotations=len(annotations), train_scenes=len(names),
    graphs_missing=len(missing), expressions_with_strict_edge=len(rows),
    strict_edges=len(all_edges),
    expressions_with_candidate=len(identified), candidate_scenes=len(scene_counts),
    expressions_single_edge_single_candidate=len(single),
    single_candidate_scenes=len({r["scene"] for r in single}),
    zero_candidate_edges=sum(not e["candidates"] for e in all_edges),
    one_candidate_edges=sum(len(e["candidates"]) == 1 for e in all_edges),
    multiple_candidate_edges=sum(len(e["candidates"]) > 1 for e in all_edges),
    relation_counts=dict(Counter(e["relation"] for e in all_edges)),
    same_name_as_target_edges=sum(e["same_name_as_target"] for e in all_edges),
)
assert summary["strict_edges"] == sum(summary[k] for k in (
    "zero_candidate_edges", "one_candidate_edges", "multiple_candidate_edges"))
result = dict(
    summary=summary, rows=rows, missing_graphs=missing,
    scene_counts=dict(sorted(scene_counts.items())),
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), annotations_path, graphs_path)},
    limitations="Full existing TRAIN only; no native model predictions or new labels. "
    "Exact names and target-node0 assumption follow stored parser; uniqueness among "
    "annotated object names is not unique physical referent. Unmentioned objects, "
    "synonyms,plurality,partwhole and incorrect attachment remain unknown. This is "
    "potential applicability,not verified relation truth,causal benefit or novelty.")
destination = ROOT / "pipeline/relation_training_coverage_20260916"
destination.mkdir(exist_ok=True)
(destination / "result.json").write_text(json.dumps(result, indent=2))
print(json.dumps(summary, indent=2), flush=True)
