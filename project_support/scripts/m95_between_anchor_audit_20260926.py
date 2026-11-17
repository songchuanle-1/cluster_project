"""Exact two-anchor scene graph binding for five frozen failures."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


SCREEN_SHA = "69a5ea6de4ab4c72744b2431464858d19679571b79956752b9f44d71ac482725"
MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def norm(text):
    return " ".join(re.findall(r"[a-z]+", str(text).lower()))


def main():
    p = argparse.ArgumentParser()
    for name in ("screen", "manifest", "source", "graphs", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    if digest(a.screen) != SCREEN_SHA or digest(a.manifest) != MANIFEST_SHA:
        raise ValueError("Frozen input hash differs")
    screen = json.loads(a.screen.read_text(encoding="utf-8"))
    manifest = {int(r["manifest_index"]): r for r in
                json.loads(a.manifest.read_text(encoding="utf-8"))["rows"]}
    source = json.loads(a.source.read_text(encoding="utf-8"))
    graphs = json.loads(a.graphs.read_text(encoding="utf-8"))
    names = defaultdict(lambda: defaultdict(set))
    for item in source:
        names[item["scene_id"]][norm(item["object_name"])].add(str(item["object_id"]))
    rows = []
    for row in screen["rows"]:
        if not row["between"] or not row["failed"]:
            continue
        index = int(row["manifest_index"])
        entry = manifest[index]
        scene = entry["scene_id"]
        if row["scene"] != scene:
            raise ValueError("Scene binding differs")
        graph = graphs[scene][str(entry["ann_id"])]
        edges = [e for e in graph["graph_edge"]
                 if "between" in norm(e.get("relation", "")).split()]
        resolved = []
        for edge in edges:
            anchors = sorted(names[scene].get(norm(edge.get("subject", "")), set()))
            resolved.append({
                "object": edge["object"], "relation": edge["relation"],
                "subject": edge["subject"], "object_ids": anchors,
                "target_class_mentioned": norm(entry["target_class"]) in norm(edge["object"]),
            })
        exact = [e for e in resolved if e["target_class_mentioned"]
                 and len(e["object_ids"]) == 1]
        anchor_ids = {e["object_ids"][0] for e in exact}
        rows.append({
            "manifest_index": index, "scene": scene, "stratum": row["stratum"],
            "target_class": entry["target_class"], "target_object_id": entry["target_object_id"],
            "between_edges": resolved, "two_unique_target_bound_anchors": len(anchor_ids) >= 2,
        })
    if len(rows) != 5:
        raise ValueError("Five-row failure cohort differs")
    result = {
        "contract": "m95_two_anchor_resolvability_v1",
        "screen_sha256": SCREEN_SHA, "manifest_sha256": MANIFEST_SHA,
        "source_sha256": digest(a.source), "graphs_sha256": digest(a.graphs),
        "rows": rows, "failed_rows": len(rows),
        "two_unique_target_bound": sum(r["two_unique_target_bound_anchors"] for r in rows),
        "admission": False,
    }
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps({"failed_rows": len(rows),
                      "two_unique_target_bound": result["two_unique_target_bound"]}))


if __name__ == "__main__":
    main()
