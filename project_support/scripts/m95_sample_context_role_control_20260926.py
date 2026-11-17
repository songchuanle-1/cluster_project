"""Role/complexity control for exact auxiliary class-word supervision screen."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

GRAPH_SHA = "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def bound_words(graph, node):
    caption = graph["utterance"]
    spans = []
    for start, end in node.get("target_char_span", []):
        if not 0 <= int(start) < int(end) <= len(caption):
            raise ValueError("Invalid graph span")
        spans.append(caption[int(start):int(end)])
    return set().union(*(words(span) for span in spans)) if spans else set()


def analyze(screen, graphs):
    rows = []
    for original in screen["rows"]:
        graph = graphs[original["scene"]][str(original["ann_id"])]
        nodes = graph["graph_node"]
        target = [node for node in nodes if int(node["node_id"]) == 0]
        if len(target) != 1:
            raise ValueError("Target graph role not unique")
        target_words = bound_words(graph, target[0])
        others = [node for node in nodes if int(node["node_id"]) != 0
                  and node.get("node_type") == "Object"]
        other_words = set().union(*(bound_words(graph, node) for node in others)) if others else set()
        matched = set(original["matched_class_keys"])
        other_only = sorted((matched & other_words) - target_words)
        target_keys = sorted(matched & target_words)
        unbound = sorted(matched - target_words - other_words)
        count = len(re.findall(r"[a-z0-9]+", graph["utterance"].lower())) + 2
        length_bin = "short" if count <= 20 else "middle" if count <= 40 else "long"
        node_bin = "one" if len(others) == 0 else "two" if len(others) == 1 else "many"
        rows.append({
            "manifest_index": original["manifest_index"], "scene": original["scene"],
            "ann_id": original["ann_id"], "stratum": original["stratum"],
            "failed": original["failed"], "target_key": original["target_key"],
            "other_only_keys": other_only, "target_span_keys": target_keys,
            "unbound_keys": unbound, "other_node_count": len(others),
            "word_count": count, "length_bin": length_bin, "node_bin": node_bin,
            "exposed": bool(other_only),
        })
    rows.sort(key=lambda row: row["manifest_index"])
    if len(rows) != 256:
        raise ValueError("Frozen row count differs")

    def tally(items):
        return {"rows": len(items), "failures": sum(r["failed"] for r in items),
                "scenes": len({r["scene"] for r in items})}

    ambiguous = [r for r in rows if r["stratum"] == "ambiguous"]
    cells = defaultdict(list)
    for row in ambiguous:
        cells[(row["node_bin"], row["length_bin"], row["exposed"])].append(row)
    matched = {
        (node, length): (tally(cells[(node, length, True)]),
                         tally(cells[(node, length, False)]))
        for node in ("one", "two", "many")
        for length in ("short", "middle", "long")
    }
    matched_cells = [
        {"node_bin": node, "length_bin": length, "exposed": yes, "control": no}
        for (node, length), (yes, no) in matched.items() if yes["rows"] and no["rows"]
    ]
    return {
        "contract": "m95_sample_context_role_control_v1", "admission": False,
        "graph_sha256": GRAPH_SHA, "screen_sha256": screen.get("_sha256"),
        "summary": {
            "ambiguous": tally(ambiguous),
            "other_only": tally([r for r in ambiguous if r["exposed"]]),
            "non_exposed": tally([r for r in ambiguous if not r["exposed"]]),
            "other_node_no_other_class": tally(
                [r for r in ambiguous if r["other_node_count"] and not r["exposed"]]),
            "target_span_key": tally([r for r in ambiguous if r["target_span_keys"]]),
            "unbound_key": tally([r for r in ambiguous if r["unbound_keys"]]),
            "matched_cells": matched_cells,
            "matched_exposed_rows": sum(c["exposed"]["rows"] for c in matched_cells),
            "matched_control_rows": sum(c["control"]["rows"] for c in matched_cells),
            "all_cells": [
                {"node_bin": node, "length_bin": length, "exposed": exposed,
                 **tally(cells[(node, length, exposed)])}
                for node in ("one", "two", "many")
                for length in ("short", "middle", "long")
                for exposed in (True, False)],
        }, "rows": rows,
    }


def main():
    p = argparse.ArgumentParser()
    for name in ("screen", "graphs", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or sha(args.graphs) != GRAPH_SHA:
        raise ValueError("Output exists or graph hash differs")
    screen = json.loads(args.screen.read_text(encoding="utf-8"))
    if screen.get("contract") != "m95_sample_context_support_v1":
        raise ValueError("Unexpected screen")
    screen["_sha256"] = sha(args.screen)
    result = analyze(screen, json.loads(args.graphs.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
