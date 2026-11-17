"""Read-only original-description versus native graph-utterance audit."""
import argparse
import difflib
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


def words(value):
    return re.findall(r"[a-z0-9]+", value.lower())


def audit(cohort, source, graphs):
    descriptions = defaultdict(list)
    for item in source:
        descriptions[(item["scene_id"], int(item["ann_id"]), str(item["object_id"]))].append(item)
    rows = []
    for item in cohort["rows"]:
        key = item["scene"], int(item["ann_id"]), str(item["target"])
        if len(descriptions[key]) != 1:
            raise ValueError("Source identity not unique")
        original = descriptions[key][0]["description"]
        graph = graphs[key[0]][str(key[1])]["utterance"]
        left, right = words(original), words(graph)
        edits = [
            {"type": kind, "source": left[i:j], "graph": right[k:l]}
            for kind, i, j, k, l in difflib.SequenceMatcher(
                a=left, b=right, autojunk=False).get_opcodes()
            if kind != "equal"
        ]
        rows.append({
            "manifest_index": item["manifest_index"], "scene": key[0],
            "ann_id": key[1], "target": key[2], "stratum": item["stratum"],
            "failed": bool(item["failed"]),
            "source_description": original, "graph_utterance": graph,
            "normalized_exact": " ".join(original.lower().split()) == " ".join(graph.lower().split()),
            "tokens_equal": left == right, "edits": edits,
        })
    rows.sort(key=lambda item: item["manifest_index"])
    if len(rows) != 256 or [r["manifest_index"] for r in rows] != list(range(256)):
        raise ValueError("Frozen cohort incomplete")

    def summary(items):
        return {"rows": len(items), "scenes": len({r["scene"] for r in items}),
                "failures": sum(r["failed"] for r in items),
                "normalized_different": sum(not r["normalized_exact"] for r in items),
                "word_changed": sum(not r["tokens_equal"] for r in items),
                "word_changed_failures": sum(not r["tokens_equal"] and r["failed"] for r in items),
                "punctuation_only": sum(not r["normalized_exact"] and r["tokens_equal"] for r in items)}

    groups = defaultdict(list)
    for row in rows:
        groups[(row["scene"], row["stratum"])].append(row)
    pairs = [(a, b) for group in groups.values() for index, a in enumerate(group)
             for b in group[index + 1:] if a["tokens_equal"] != b["tokens_equal"]]
    return {
        "contract": "m95_utterance_provenance_v1", "admission": False,
        "source_sha256": SOURCE_SHA, "graph_sha256": GRAPH_SHA,
        "capture_sha256": CAPTURE_SHA,
        "summary": {
            "all": summary(rows),
            "ambiguous": summary([r for r in rows if r["stratum"] == "ambiguous"]),
            "class_unique": summary([r for r in rows if r["stratum"] == "class_unique"]),
            "same_scene_discordant_pairs": len(pairs),
            "same_scene_word_changed_failures": sum(
                a["failed"] if not a["tokens_equal"] else b["failed"] for a, b in pairs),
            "same_scene_unchanged_failures": sum(
                b["failed"] if not a["tokens_equal"] else a["failed"] for a, b in pairs),
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
        raise ValueError("Frozen capture differs")
    result = audit(cohort, json.loads(args.source.read_text(encoding="utf-8")),
                   json.loads(args.graphs.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
