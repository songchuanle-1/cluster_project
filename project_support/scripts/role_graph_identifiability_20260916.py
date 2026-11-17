"""Connectivity evidence, not a coreference solver or automatic labels."""
import hashlib
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "pipeline/reports"
path = root / "role_graphs_20260916.json"
data = json.loads(path.read_text())
rows = []
for record in data["rows"]:
    graph = record["graph"]
    nodes = {n["node_id"]: n for n in graph["graph_node"]}
    main = nodes[0]
    adjacency = {i: set() for i in nodes}
    for edge in graph["graph_edge"]:
        a, b = edge["obj_idx"], edge["sub_idx"]
        assert a in nodes and b in nodes
        adjacency[a].add(b)
        adjacency[b].add(a)
    reached, todo = {0}, [0]
    while todo:
        for nxt in adjacency[todo.pop()]:
            if nxt not in reached:
                reached.add(nxt)
                todo.append(nxt)
    for i, node in nodes.items():
        if i == 0 or node.get("lemma_head") != main.get("lemma_head"):
            continue
        if node.get("node_type") != "Object":
            continue
        rows.append(dict(scene=record["scene"], ann_id=record["ann_id"], node=i,
                         target=node["target"], main_target=main["target"],
                         reachable=i in reached, direct_edge=i in adjacency[0],
                         utterance=graph["utterance"],
                         selected_iou=record["selected_iou"]))
# Instance inequality cannot be represented by target-membership inequality.
target, anchor_a, anchor_b = 42, 4, 9
assert anchor_a != anchor_b
assert (anchor_a == target) == (anchor_b == target) == False
# Disconnected graph labels alone admit both repeated and distinct referents.
assign_same, assign_other = {0: target, 1: anchor_a, 2: target, 3: anchor_a}, {
    0: target, 1: anchor_a, 2: anchor_b, 3: anchor_a}
edges = [(0, 1), (2, 3)]
assert all(a[x] != a[y] for x, y in edges for a in (assign_same, assign_other))
summary = dict(expressions=len({(r["scene"], r["ann_id"]) for r in rows}),
               repeated_nodes=len(rows), reachable=sum(r["reachable"] for r in rows),
               disconnected=sum(not r["reachable"] for r in rows),
               direct=sum(r["direct_edge"] for r in rows))
report = dict(summary=summary, rows=rows, controls="PASS",
              source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
              conclusion="Connectivity alone does not identify coreference. Even assuming "
              "irreflexive relations cannot distinguish the two constructed assignments. "
              "Reject binary role graph coloring and bare latent likelihood as standalone core.",
              scope="Existing fixed TRAIN parse graphs;no true-coreference labels or model efficacy.")
(root / "role_graph_identifiability_20260916.json").write_text(json.dumps(report, indent=2))
print(json.dumps(summary))
