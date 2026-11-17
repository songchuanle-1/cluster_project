"""Audit existing TRAIN graph ownership; no inferred labels or model changes."""
import hashlib
import json
from pathlib import Path

ROOT = Path("/data3/songcl/Project/Cluster_project")
source = ROOT / "pipeline/instance_feature_audit_20260916/result.json"
graphs_path = Path("/data3/songcl/data/data_cluster/scanrefer/scene_graphs_new_train.json")
graphs = json.loads(graphs_path.read_text())
prior = json.loads(source.read_text())["rows"]
rows = []
for old in prior:
    graph = graphs[old["scene"]][str(old["ann_id"])]
    caption = " ".join(graph["utterance"].replace(",", " ,").split())
    entities = []
    for node in graph["graph_node"]:
        if node["node_type"] != "Object":
            continue
        spans = {}
        for key in ("target_char_span", "mod_char_span", "rel_char_span"):
            spans[key] = [
                dict(span=span, text=caption[int(span[0]):int(span[1])],
                     valid=0 <= int(span[0]) < int(span[1]) <= len(caption))
                for span in node[key]
            ]
        entities.append(dict(node_id=node["node_id"], spans=spans))
    non_target = [e for e in entities if e["node_id"] != 0]
    rows.append(dict(
        scene=old["scene"], ann_id=old["ann_id"], caption=caption,
        target=old["target"], winner=old["winner"],
        success=old["before"] > .5,
        confident_wrong=old["before"] <= .5 and old["winner_overlap"] > .5
        and old["winner"] != old["target"],
        entities=entities, edges=graph["graph_edge"],
        non_target_entities=len(non_target),
        non_target_with_attributes=sum(bool(e["spans"]["mod_char_span"]) for e in non_target),
        invalid_spans=sum(not s["valid"] for e in entities
                          for values in e["spans"].values() for s in values),
    ))
assert len(rows) == len({(r["scene"], r["ann_id"]) for r in rows}) == 123
summary = {}
for name, items in (
    ("success", [r for r in rows if r["success"]]),
    ("confident_wrong", [r for r in rows if r["confident_wrong"]]),
    ("other_failure", [r for r in rows if not r["success"] and not r["confident_wrong"]]),
):
    summary[name] = dict(
        expressions=len(items),
        with_non_target_attributes=sum(r["non_target_with_attributes"] > 0 for r in items),
        multiple_non_target_entities=sum(r["non_target_entities"] >= 2 for r in items),
        invalid_spans=sum(r["invalid_spans"] for r in items),
    )
out = ROOT / "pipeline/entity_binding_20260916"
out.mkdir(exist_ok=True)
result = dict(
    rows=rows, summary=summary,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), source, graphs_path)},
    limitations="Fixed123 TRAIN expressions. Graph ownership is parser output, not "
    "verified visual entity grounding. Attributes of non-target nodes omitted from "
    "dense supervision do not establish absence from contextual text embeddings. "
    "No model forward, new annotation, efficacy or novelty claim.",
)
(out / "result.json").write_text(json.dumps(result, indent=2))
print(json.dumps(summary), flush=True)
