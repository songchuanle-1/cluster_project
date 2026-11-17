"""Native parsed target-node binding for frozen ordinal expressions."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


SCREEN_SHA = "636244ffed4528086f1da37ef9063ff546c1e8ceafed8119c77ff520cf5cc4f7"
MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
STRICT = {"first", "second", "third", "last"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    for name in ("screen", "manifest", "source", "graphs", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    if digest(a.screen) != SCREEN_SHA or digest(a.manifest) != MANIFEST_SHA:
        raise ValueError("Frozen input differs")
    screen = json.loads(a.screen.read_text(encoding="utf-8"))
    manifest = {int(r["manifest_index"]): r for r in
                json.loads(a.manifest.read_text(encoding="utf-8"))["rows"]}
    source = json.loads(a.source.read_text(encoding="utf-8"))
    graphs = json.loads(a.graphs.read_text(encoding="utf-8"))
    descriptions = defaultdict(list)
    for item in source:
        descriptions[(item["scene_id"], int(item["ann_id"]), str(item["object_id"]))].append(
            item["description"])
    rows = []
    for row in screen["rows"]:
        if row["stratum"] != "ambiguous" or not row["ordinal_words"]:
            continue
        index = int(row["manifest_index"])
        entry = manifest[index]
        key = (entry["scene_id"], int(entry["ann_id"]), str(entry["target_object_id"]))
        if len(descriptions[key]) != 1 or key[0] != row["scene"]:
            raise ValueError("Frozen description binding differs")
        graph = graphs[key[0]][str(key[1])]
        nodes = [{"node_id": node.get("node_id"), "target": node.get("target"),
                  "mod_text": node.get("mod_text"), "node_type": node.get("node_type")}
                 for node in graph["graph_node"]]
        edges = [{"relation": edge.get("relation"), "object": edge.get("object"),
                  "subject": edge.get("subject"), "obj_idx": edge.get("obj_idx")}
                 for edge in graph["graph_edge"]]
        strict = bool(set(row["ordinal_words"]) & STRICT)
        target_mod = any(
            node["node_id"] == 0 and
            any(word in " ".join(str(x).lower() for x in (node["mod_text"] or []))
                for word in (set(row["ordinal_words"]) & STRICT))
            for node in nodes)
        rows.append({
            "manifest_index": index, "scene": row["scene"], "failed": row["failed"],
            "ordinal_words": row["ordinal_words"], "strict_sequence": strict,
            "same_class_peer_count": entry["same_class_peer_count"],
            "target_modifier_bound": target_mod, "description": descriptions[key][0],
            "nodes": nodes, "edges": edges,
        })
    if len(rows) != 9:
        raise ValueError("Nine-row ambiguous ordinal cohort differs")
    result = {"contract": "m95_ordinal_target_binding_v1",
              "screen_sha256": SCREEN_SHA, "manifest_sha256": MANIFEST_SHA,
              "source_sha256": digest(a.source), "graphs_sha256": digest(a.graphs),
              "rows": rows, "ambiguous_rows": len(rows),
              "strict_rows": sum(r["strict_sequence"] for r in rows),
              "strict_failed": sum(r["strict_sequence"] and r["failed"] for r in rows),
              "strict_target_modifier_bound": sum(r["strict_sequence"] and
                                                  r["target_modifier_bound"] for r in rows),
              "admission": False}
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps({k: result[k] for k in ("ambiguous_rows", "strict_rows",
                                           "strict_failed", "strict_target_modifier_bound")}))


if __name__ == "__main__":
    main()
