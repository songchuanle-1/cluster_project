"""Exact native scene-graph binding for frozen independent group cohorts."""
import argparse
import json
import re
from pathlib import Path

from m95_group_holdout_20260926 import digest

LOWER_SHA = "ecf6d9fe21f254e512b4fc490bc8a843a256a0a8c9e8ae5cab79c86bbf894edc"
UPPER_SHA = "e86746aac35cae5e3a47e6cf277bdc67fbd4dc14efb4ddc9811f68d499bbbe85"
GRAPHS_SHA = "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"
CUES = {"lower": frozenset(("bottom", "lower")),
        "upper": frozenset(("top", "upper"))}


def words(text):
    if isinstance(text, list):
        text = " ".join(str(item) for item in text)
    return set(re.findall(r"[a-z]+", str(text).lower()))


def audit(lower, upper, graphs):
    rows = []
    for cohort, document in (("lower", lower), ("upper", upper)):
        for item in document["rows"]:
            scene, ann = item["scene"], str(item["ann_id"])
            if scene not in graphs or ann not in graphs[scene]:
                raise ValueError("Missing parsed graph: " + scene + "/" + ann)
            graph = graphs[scene][ann]
            nodes = [{"node_id": n.get("node_id"), "target": n.get("target"),
                      "mod_text": n.get("mod_text"), "node_type": n.get("node_type")}
                     for n in graph["graph_node"]]
            edges = [{"object": e.get("object"), "subject": e.get("subject"),
                      "relation": e.get("relation"), "obj_idx": e.get("obj_idx")}
                     for e in graph["graph_edge"]]
            cue = CUES[cohort]
            rows.append({"cohort": cohort, "scene": scene, "ann_id": item["ann_id"],
                         "target": item["target"], "object_name": item["object_name"],
                         "target_modifier_cue": any(
                             n["node_id"] == 0 and bool(words(n["mod_text"]) & cue)
                             for n in nodes),
                         "other_modifier_cue": any(
                             n["node_id"] != 0 and bool(words(n["mod_text"]) & cue)
                             for n in nodes),
                         "edge_relation_cue": any(
                             bool(words(e["relation"]) & cue) for e in edges),
                         "nodes": nodes, "edges": edges})
    summary = {}
    for cohort in CUES:
        chosen = [r for r in rows if r["cohort"] == cohort]
        summary[cohort] = {
            "rows": len(chosen),
            "unique_scene_targets": len({(r["scene"], r["target"]) for r in chosen}),
            "target_modifier": sum(r["target_modifier_cue"] for r in chosen),
            "other_modifier": sum(r["other_modifier_cue"] for r in chosen),
            "edge_relation": sum(r["edge_relation_cue"] for r in chosen),
        }
    return {"rows": rows, "summary": summary}


def main():
    p = argparse.ArgumentParser()
    for name in ("lower", "upper", "graphs", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    for path, expected in ((a.lower, LOWER_SHA), (a.upper, UPPER_SHA),
                           (a.graphs, GRAPHS_SHA)):
        if digest(path) != expected:
            raise ValueError("Frozen input differs: " + str(path))
    result = audit(json.loads(a.lower.read_text(encoding="utf-8")),
                   json.loads(a.upper.read_text(encoding="utf-8")),
                   json.loads(a.graphs.read_text(encoding="utf-8")))
    result.update({"contract": "m95_group_graph_binding_v1", "admission": False,
                   "lower_sha256": LOWER_SHA, "upper_sha256": UPPER_SHA,
                   "graphs_sha256": GRAPHS_SHA})
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
