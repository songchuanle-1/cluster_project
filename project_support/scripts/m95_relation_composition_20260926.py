"""Prediction-blind graph-path structure screen on frozen M95 TRAIN cohort."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

GRAPH_SHA = "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"
CAPTURE_SHA = "5a1ddd9a906983416adbfb0e9d03b386de92a21803fdf20afe40740b5a69687e"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(graph):
    nodes = {int(n["node_id"]): n for n in graph["graph_node"]}
    if 0 not in nodes or nodes[0]["node_type"] != "Object":
        return {"valid": False, "reason": "no object target"}
    edges = []
    for e in graph["graph_edge"]:
        # Fail closed on an unfamiliar edge schema rather than invent a path.
        if not {"sub_idx", "obj_idx"} <= e.keys():
            return {"valid": False, "reason": "unknown edge schema"}
        src, dst = int(e["sub_idx"]), int(e["obj_idx"])
        if src not in nodes or dst not in nodes:
            return {"valid": False, "reason": "missing edge node"}
        edges.append((src, dst))
    paths = {(a, b) for src, a in edges if src == 0
             for middle, b in edges if middle == a and b != 0 and b != a}
    return {"valid": True, "edge_count": len(edges),
            "target_edge_count": sum(src == 0 for src, _ in edges),
            "multi_hop": bool(paths),
            "reference_count": len({n for _, n in edges if n != 0}),
            "paths": sorted([list(pair) for pair in paths])}


def analyze(cohort, graphs):
    rows = []
    for item in cohort["rows"]:
        key = item["scene"], str(item["ann_id"])
        entry = inspect(graphs[key[0]][key[1]])
        rows.append({"manifest_index": item["manifest_index"], "scene": key[0],
                     "ann_id": item["ann_id"], "stratum": item["stratum"],
                     "failed": item["failed"], **entry})
    if len(rows) != 256 or len({r["manifest_index"] for r in rows}) != 256:
        raise ValueError("Incomplete frozen cohort")

    def tally(items):
        return {"rows": len(items), "failures": sum(r["failed"] for r in items),
                "scenes": len({r["scene"] for r in items})}

    def breakdown(items):
        valid = [r for r in items if r["valid"]]
        return {
            "all": tally(items),
            "unresolved": tally([r for r in items if not r["valid"]]),
            "multi_hop": tally([r for r in valid if r["multi_hop"]]),
            "single_target_edge": tally([r for r in valid if r["edge_count"] == 1 and r["target_edge_count"] == 1]),
            "multi_edge_nonpath": tally([r for r in valid if r["edge_count"] >= 2 and not r["multi_hop"]]),
            "zero_edge": tally([r for r in valid if r["edge_count"] == 0]),
        }

    scenes = defaultdict(list)
    for row in rows:
        if row["valid"]:
            scenes[(row["scene"], row["stratum"])].append(row)
    pairs = [(a, b) for group in scenes.values() for a in group for b in group
             if a["manifest_index"] < b["manifest_index"] and a["multi_hop"] != b["multi_hop"]]
    return {"contract": "m95_relation_composition_v1", "admission": False,
            "graph_sha256": GRAPH_SHA, "capture_sha256": CAPTURE_SHA,
            "summary": {
                "all": breakdown(rows),
                "ambiguous": breakdown([r for r in rows if r["stratum"] == "ambiguous"]),
                "class_unique": breakdown([r for r in rows if r["stratum"] == "class_unique"]),
                "same_scene_discordant_pairs": len(pairs),
                "same_scene_exposed_failures": sum(a["failed"] if a["multi_hop"] else b["failed"] for a, b in pairs),
                "same_scene_control_failures": sum(b["failed"] if a["multi_hop"] else a["failed"] for a, b in pairs),
            }, "rows": rows}


def main():
    p = argparse.ArgumentParser()
    for name in ("graphs", "cohort", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    if sha(args.graphs) != GRAPH_SHA:
        raise ValueError("Graph SHA differs")
    cohort = json.loads(args.cohort.read_text(encoding="utf-8"))
    if cohort.get("capture_sha256") != CAPTURE_SHA:
        raise ValueError("Cohort capture differs")
    result = analyze(cohort, json.loads(args.graphs.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
