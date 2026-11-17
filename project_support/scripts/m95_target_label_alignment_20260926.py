"""Read-only target category/parsed target alignment audit on frozen TRAIN rows."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

SOURCE_SHA = "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
GRAPH_SHA = "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"
CAPTURE_SHA = "5a1ddd9a906983416adbfb0e9d03b386de92a21803fdf20afe40740b5a69687e"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(text):
    words = re.findall(r"[a-z0-9]+", str(text).lower().replace("_", " "))
    return " ".join(w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words)


def summarize(rows):
    return {
        "rows": len(rows),
        "scenes": len({r["scene"] for r in rows}),
        "failures": sum(r["failed"] for r in rows),
        "unresolved": sum(r["unresolved"] for r in rows),
        "mismatches": sum(r["mismatch"] for r in rows),
        "mismatch_failures": sum(r["mismatch"] and r["failed"] for r in rows),
        "aligned_failures": sum(not r["mismatch"] and not r["unresolved"] and r["failed"] for r in rows),
        "other_node_different": sum(r["other_node_different"] for r in rows),
    }


def audit(cohort, source, graphs):
    descriptions = defaultdict(list)
    for item in source:
        descriptions[(item["scene_id"], int(item["ann_id"]), str(item["object_id"]))].append(item)
    rows = []
    for item in cohort["rows"]:
        key = item["scene"], int(item["ann_id"]), str(item["target"])
        if len(descriptions[key]) != 1:
            raise ValueError("Non-unique frozen source identity: " + repr(key))
        graph = graphs[key[0]][str(key[1])]
        targets = [n for n in graph["graph_node"] if int(n["node_id"]) == 0]
        if len(targets) != 1:
            raise ValueError("Non-unique graph target: " + repr(key))
        node = targets[0]
        label = normalize(descriptions[key][0]["object_name"])
        lemma = normalize(node.get("lemma_head", ""))
        unresolved = not label or not lemma or node.get("node_type") != "Object"
        rows.append({
            "manifest_index": item["manifest_index"],
            "scene": key[0], "ann_id": key[1], "target": key[2],
            "stratum": item["stratum"], "failed": bool(item["failed"]),
            "object_name": descriptions[key][0]["object_name"],
            "description": descriptions[key][0]["description"],
            "graph_utterance": graph["utterance"],
            "lemma_head": node.get("lemma_head", ""),
            "target_spans": node.get("target_char_span", []),
            "unresolved": bool(unresolved),
            "mismatch": bool(not unresolved and label != lemma),
            "other_node_different": any(
                n.get("node_type") == "Object" and
                normalize(n.get("lemma_head", "")) != label
                for n in graph["graph_node"] if int(n["node_id"]) != 0
            ),
        })
    rows.sort(key=lambda row: row["manifest_index"])
    if len(rows) != 256 or [row["manifest_index"] for row in rows] != list(range(256)):
        raise ValueError("Frozen capture incomplete")
    scenes = defaultdict(list)
    for row in rows:
        if not row["unresolved"]:
            scenes[(row["scene"], row["stratum"])].append(row)
    pairs = [(a, b) for group in scenes.values() for index, a in enumerate(group)
             for b in group[index + 1:] if a["mismatch"] != b["mismatch"]]
    return {
        "contract": "m95_target_label_alignment_v1", "admission": False,
        "source_sha256": SOURCE_SHA, "graph_sha256": GRAPH_SHA,
        "capture_sha256": CAPTURE_SHA,
        "summary": {
            "all": summarize(rows),
            "ambiguous": summarize([r for r in rows if r["stratum"] == "ambiguous"]),
            "class_unique": summarize([r for r in rows if r["stratum"] == "class_unique"]),
            "same_scene_discordant_pairs": len(pairs),
            "same_scene_mismatch_failures": sum(
                a["failed"] if a["mismatch"] else b["failed"] for a, b in pairs),
            "same_scene_aligned_failures": sum(
                b["failed"] if a["mismatch"] else a["failed"] for a, b in pairs),
        },
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("source", "graphs", "cohort", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    if sha(args.source) != SOURCE_SHA or sha(args.graphs) != GRAPH_SHA:
        raise ValueError("Native source hash differs")
    cohort = json.loads(args.cohort.read_text(encoding="utf-8"))
    if cohort.get("capture_sha256") != CAPTURE_SHA:
        raise ValueError("Frozen cohort differs")
    result = audit(cohort, json.loads(args.source.read_text(encoding="utf-8")),
                   json.loads(args.graphs.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
