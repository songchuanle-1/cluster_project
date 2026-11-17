"""Read-only literal graph target span/lemma consistency audit."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

GRAPH_SHA = "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"
CAPTURE_SHA = "5a1ddd9a906983416adbfb0e9d03b386de92a21803fdf20afe40740b5a69687e"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tokens(text):
    return [w[:-1] if len(w) > 3 and w.endswith("s") else w
            for w in re.findall(r"[a-z0-9]+", text.lower())]


def subsequence(needle, haystack):
    return any(haystack[i:i + len(needle)] == needle
               for i in range(len(haystack) - len(needle) + 1))


def audit(cohort, graphs):
    rows = []
    for item in cohort["rows"]:
        graph = graphs[item["scene"]][str(item["ann_id"])]
        nodes = [node for node in graph["graph_node"] if int(node["node_id"]) == 0]
        if len(nodes) != 1:
            raise ValueError("Non-unique graph target")
        node = nodes[0]
        utterance = graph["utterance"]
        spans = []
        for begin, end in node.get("target_char_span", []):
            begin, end = int(begin), int(end)
            if not 0 <= begin < end <= len(utterance):
                raise ValueError("Invalid target span")
            spans.append(utterance[begin:end])
        lemma = tokens(str(node.get("lemma_head", "")))
        parts = [tokens(text) for text in spans]
        unresolved = not spans or not lemma or node.get("node_type") != "Object"
        exact = bool(not unresolved and any(subsequence(lemma, part) for part in parts))
        head = bool(not unresolved and any(lemma[-1] in part for part in parts))
        rows.append({
            "manifest_index": item["manifest_index"], "scene": item["scene"],
            "ann_id": item["ann_id"], "stratum": item["stratum"],
            "failed": bool(item["failed"]), "lemma_head": node.get("lemma_head", ""),
            "span_texts": spans, "unresolved": bool(unresolved),
            "exact": exact, "head": head,
            "exposed": bool(not unresolved and not exact and not head),
        })
    rows.sort(key=lambda row: row["manifest_index"])
    if len(rows) != 256 or [r["manifest_index"] for r in rows] != list(range(256)):
        raise ValueError("Frozen capture incomplete")

    def summary(items):
        return {"rows": len(items), "scenes": len({r["scene"] for r in items}),
                "failures": sum(r["failed"] for r in items),
                "unresolved": sum(r["unresolved"] for r in items),
                "exact": sum(r["exact"] for r in items),
                "head": sum(r["head"] for r in items),
                "exposed": sum(r["exposed"] for r in items),
                "exposed_failures": sum(r["exposed"] and r["failed"] for r in items)}

    scenes = defaultdict(list)
    for row in rows:
        if not row["unresolved"]:
            scenes[(row["scene"], row["stratum"])].append(row)
    pairs = [(a, b) for group in scenes.values() for index, a in enumerate(group)
             for b in group[index + 1:] if a["exposed"] != b["exposed"]]
    return {
        "contract": "m95_target_span_lemma_v1", "admission": False,
        "graph_sha256": GRAPH_SHA, "capture_sha256": CAPTURE_SHA,
        "summary": {
            "all": summary(rows),
            "ambiguous": summary([r for r in rows if r["stratum"] == "ambiguous"]),
            "class_unique": summary([r for r in rows if r["stratum"] == "class_unique"]),
            "same_scene_discordant_pairs": len(pairs),
            "same_scene_exposed_failures": sum(
                a["failed"] if a["exposed"] else b["failed"] for a, b in pairs),
            "same_scene_control_failures": sum(
                b["failed"] if a["exposed"] else a["failed"] for a, b in pairs),
        }, "rows": rows,
    }


def main():
    p = argparse.ArgumentParser()
    for name in ("graphs", "cohort", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or sha(args.graphs) != GRAPH_SHA:
        raise ValueError("Output exists or graph hash differs")
    cohort = json.loads(args.cohort.read_text(encoding="utf-8"))
    if cohort.get("capture_sha256") != CAPTURE_SHA:
        raise ValueError("Frozen capture differs")
    result = audit(cohort, json.loads(args.graphs.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
