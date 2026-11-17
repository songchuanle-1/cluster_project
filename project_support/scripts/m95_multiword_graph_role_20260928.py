"""Bind frozen phrase exposure to native graph mention spans."""
import argparse
import hashlib
import json
import re
from pathlib import Path


PHYSICAL_SHA = "331718c7181f176197502e74ea0cf271025096cc0bd9c464348c8944674caaf0"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-root", type=Path, required=True)
    p.add_argument("--physical-report", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or sha(args.physical_report) != PHYSICAL_SHA:
        raise ValueError("Physical report differs or output exists")
    report = json.loads(args.physical_report.read_text())
    graph_path = args.data_root / "scanrefer/scene_graphs_new_train.json"
    if (report["contract"] != "m95_multiword_context_v1"
            or report["inputs"]["graphs"] != sha(graph_path)
            or len(report["exposed_rows"]) != 11):
        raise ValueError("Graph binding differs")
    graphs = json.loads(graph_path.read_text())
    rows = []
    for record in report["exposed_rows"]:
        scene, aid = record["scene"], int(record["ann_id"])
        graph = graphs[scene][str(aid)]
        caption = graph["utterance"]
        mentions = []
        matches = list(re.finditer(r"(?<![A-Za-z])shower\s+curtain(?![A-Za-z])", caption))
        if not matches:
            raise ValueError("No original phrase")
        for match in matches:
            roles = set()
            for node in graph["graph_node"]:
                node_id = int(node["node_id"])
                for raw in node.get("target_char_span", []):
                    start, end = map(int, raw)
                    if not (0 <= start < end <= len(caption)):
                        raise ValueError("Invalid graph span")
                    if match.start() < end and start < match.end():
                        if node_id == 0:
                            roles.add("target")
                        elif node.get("node_type") == "Object":
                            roles.add("other_object")
                        else:
                            roles.add("other_node")
            mentions.append({"char_span": [match.start(), match.end()],
                             "roles": sorted(roles) if roles else ["unbound"]})
        rows.append({"scene": scene, "ann_id": aid, "mentions": mentions})
    counts = {
        "exposed_expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
        "mentions": sum(len(r["mentions"]) for r in rows),
        "other_object_mentions": sum(
            "other_object" in m["roles"] for r in rows for m in r["mentions"]),
        "target_mentions": sum("target" in m["roles"]
                               for r in rows for m in r["mentions"]),
        "unbound_mentions": sum(m["roles"] == ["unbound"]
                                for r in rows for m in r["mentions"]),
        "other_only_expressions": sum(
            all(m["roles"] == ["other_object"] for m in r["mentions"])
            for r in rows),
    }
    result = {"contract": "m95_multiword_graph_role_v1", "admission": False,
              "physical_sha256": sha(args.physical_report),
              "graph_sha256": sha(graph_path), "summary": counts,
              "rows": rows,
              "limits": "Graph linguistic spans are not physical anchors; no failure or native intervention evidence."}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
