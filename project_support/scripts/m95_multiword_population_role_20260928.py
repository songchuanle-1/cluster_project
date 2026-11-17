"""Graph-role census of frozen full-TRAIN physical multiword exposure."""
import argparse
import hashlib
import json
import re
from pathlib import Path


POP_SHA = "325626925578df183ef3f8ffdce2b7cb7f010ccefa87de70db0b4b1353f0d664"
FIRST_SHA = "49d35eae3c1b3b13c90ae483fa67d26b1e86fb94a178e2544ccfb85e96a7661d"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-root", type=Path, required=True)
    p.add_argument("--population", type=Path, required=True)
    p.add_argument("--first64-role", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if (args.output.exists() or sha(args.population) != POP_SHA
            or sha(args.first64_role) != FIRST_SHA):
        raise ValueError("Frozen reports differ or output exists")
    pop = json.loads(args.population.read_text())
    prior = json.loads(args.first64_role.read_text())
    graph_path = args.data_root / "scanrefer/scene_graphs_new_train.json"
    if (pop["contract"] != "m95_multiword_population_v1"
            or prior["contract"] != "m95_multiword_graph_role_v1"
            or pop["inputs"]["graphs"] != sha(graph_path)
            or prior["graph_sha256"] != sha(graph_path)):
        raise ValueError("Graph source differs")
    graphs = json.loads(graph_path.read_text())
    rows = []
    for item in pop["rows"]:
        if not item["other_curtain_instances"]:
            continue
        scene, aid = item["scene"], int(item["ann_id"])
        text = graphs[scene][str(aid)]["utterance"]
        mentions = []
        for match in re.finditer(r"(?<![A-Za-z])shower\s+curtain(?![A-Za-z])", text):
            roles = set()
            for node in graphs[scene][str(aid)]["graph_node"]:
                nid = int(node["node_id"])
                for raw in node.get("target_char_span", []):
                    start, end = map(int, raw)
                    if not (0 <= start < end <= len(text)):
                        raise ValueError("Graph span invalid")
                    if match.start() < end and start < match.end():
                        roles.add("target" if nid == 0 else
                                  "other_object" if node.get("node_type") == "Object"
                                  else "other_node")
            mentions.append({"char_span": [match.start(), match.end()],
                             "roles": sorted(roles) if roles else ["unbound"]})
        if not mentions:
            raise ValueError("Phrase missing")
        rows.append({"scene": scene, "ann_id": aid, "mentions": mentions})
    first = {(r["scene"], int(r["ann_id"])): r for r in prior["rows"]}
    observed = {(r["scene"], int(r["ann_id"])): r for r in rows if
                (r["scene"], int(r["ann_id"])) in first}
    if len(observed) != len(first) or any(
            observed[key]["mentions"] != original["mentions"]
            for key, original in first.items()):
        raise ValueError("First-64 role parity differs")
    summary = {
        "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
        "mentions": sum(len(r["mentions"]) for r in rows),
        "other_object_mentions": sum("other_object" in m["roles"]
                                     for r in rows for m in r["mentions"]),
        "target_mentions": sum("target" in m["roles"]
                               for r in rows for m in r["mentions"]),
        "unbound_mentions": sum(m["roles"] == ["unbound"]
                                for r in rows for m in r["mentions"]),
        "only_other_object_expressions": sum(
            all(m["roles"] == ["other_object"] for m in r["mentions"])
            for r in rows),
        "first64_parity_expressions": len(observed),
    }
    result = {"contract": "m95_multiword_population_role_v1",
              "admission": False, "population_sha256": POP_SHA,
              "first64_role_sha256": FIRST_SHA,
              "graph_sha256": sha(graph_path),
              "summary": summary, "rows": rows,
              "limits": "TRAIN graph linguistic-role scope; no physical anchor assignment, outcome, causal efficacy or admission."}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
