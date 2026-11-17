"""Prediction-blind TRAIN shape-word and parsed-target binding screen."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

CAPTURE_SHA = "5a1ddd9a906983416adbfb0e9d03b386de92a21803fdf20afe40740b5a69687e"
SOURCE_SHA = "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
GRAPH_SHA = "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"
WORDS = frozenset(("round", "circular", "cylindrical", "cylinder",
                   "rectangular", "square", "triangular", "oval",
                   "spherical", "cube", "cubical"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def words(text):
    if isinstance(text, list):
        text = " ".join(map(str, text))
    return set(re.findall(r"[a-z]+", str(text).lower())) & WORDS


def summarize(rows, field):
    yes = [r for r in rows if r[field]]
    no = [r for r in rows if not r[field]]
    return {"exposed": len(yes), "exposed_failures": sum(r["failed"] for r in yes),
            "unexposed": len(no), "unexposed_failures": sum(r["failed"] for r in no),
            "exposed_scenes": len({r["scene"] for r in yes})}


def analyze(capture, source, graphs):
    desc = defaultdict(list)
    for r in source:
        desc[(r["scene_id"], int(r["ann_id"]), str(r["object_id"]))].append(r)
    rows = []
    for r in capture["rows"]:
        key = r["scene"], int(r["ann_id"]), str(r["target_object_id"])
        if len(desc[key]) != 1:
            raise ValueError("Description identity incomplete")
        if r["scene"] not in graphs or str(r["ann_id"]) not in graphs[r["scene"]]:
            raise ValueError("Missing parsed scene graph")
        graph = graphs[r["scene"]][str(r["ann_id"])]
        nodes = graph["graph_node"]
        target = set().union(*(words(n.get("mod_text", []))
                               for n in nodes if n.get("node_id") == 0))
        other = set().union(*(words(n.get("mod_text", []))
                              for n in nodes if n.get("node_id") != 0))
        edges = set().union(*(words(e.get("relation", ""))
                              for e in graph["graph_edge"]))
        lexical = words(desc[key][0]["description"])
        if not target <= lexical:
            raise ValueError("Target binding outside expression")
        rows.append({
            "manifest_index": int(r["manifest_index"]), "scene": key[0],
            "ann_id": key[1], "target": key[2], "stratum": r["stratum"],
            "lexical": sorted(lexical), "target_modifier": sorted(target),
            "other_modifier": sorted(other), "edge": sorted(edges),
            "failed": float(r["ious"][int(r["selected_query"])]) <= .5,
        })
    rows.sort(key=lambda r: r["manifest_index"])
    if len(rows) != 256 or [r["manifest_index"] for r in rows] != list(range(256)):
        raise ValueError("Incomplete manifest capture")
    groups = defaultdict(list)
    for r in rows:
        groups[r["scene"]].append(r)
    pairs = [
        (a, b) for scene in groups.values() for i, a in enumerate(scene)
        for b in scene[i + 1:] if bool(a["target_modifier"]) != bool(b["target_modifier"])
    ]
    return {"rows": rows, "summary": {
        "all": {k: summarize(rows, k) for k in ("lexical", "target_modifier")},
        "ambiguous": {k: summarize([r for r in rows if r["stratum"] == "ambiguous"], k)
                      for k in ("lexical", "target_modifier")},
        "class_unique": {k: summarize([r for r in rows if r["stratum"] == "class_unique"], k)
                         for k in ("lexical", "target_modifier")},
        "other_modifier": sum(bool(r["other_modifier"]) for r in rows),
        "edge": sum(bool(r["edge"]) for r in rows),
        "same_scene_target_discordant_pairs": len(pairs),
        "same_scene_exposed_failures": sum(
            a["failed"] if a["target_modifier"] else b["failed"] for a, b in pairs),
        "same_scene_unexposed_failures": sum(
            b["failed"] if a["target_modifier"] else a["failed"] for a, b in pairs),
    }}


def main():
    p = argparse.ArgumentParser()
    for name in ("capture", "source", "graphs", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    for name, expected in (("capture", CAPTURE_SHA),
                           ("source", SOURCE_SHA), ("graphs", GRAPH_SHA)):
        if sha(getattr(a, name)) != expected:
            raise ValueError(name + " changed")
    result = analyze(json.loads(a.capture.read_text(encoding="utf-8")),
                     json.loads(a.source.read_text(encoding="utf-8")),
                     json.loads(a.graphs.read_text(encoding="utf-8")))
    result.update(contract="m95_shape_evidence_screen_v1", admission=False,
                  capture_sha256=CAPTURE_SHA, source_sha256=SOURCE_SHA,
                  graph_sha256=GRAPH_SHA)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
