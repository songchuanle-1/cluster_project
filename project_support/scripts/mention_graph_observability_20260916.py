"""Static rooted-graph observability, not native grounding or role labels."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def colors(entities, edges, rounds=2):
    """Exact tuple refinement avoids hash collisions and preserves edge direction."""
    current = {
        e["node_id"]: (
            tuple(s["text"].lower() for s in e["spans"]["target_char_span"]),
            tuple(sorted(s["text"].lower() for s in e["spans"]["mod_char_span"])),
        )
        for e in entities
    }
    history = [current]
    dangling = []
    valid = []
    for edge in edges:
        a, b = edge["obj_idx"], edge["sub_idx"]
        if a not in current or b not in current:
            dangling.append(edge)
        else:
            valid.append((a, b, edge["relation"].lower()))
    for _ in range(rounds):
        nxt = {}
        for node in current:
            neighbors = []
            for a, b, relation in valid:
                if a == node:
                    neighbors.append(("out", relation, current[b]))
                if b == node:
                    neighbors.append(("in", relation, current[a]))
            nxt[node] = (current[node], tuple(sorted(neighbors)))
        current = nxt
        history.append(current)
    return history, dangling


def entity(node, name="chair", attribute=None):
    return {"node_id": node, "spans": {
        "target_char_span": [{"text": name}],
        "mod_char_span": [] if attribute is None else [{"text": attribute}],
    }}


def edge(a, b, relation="near"):
    return {"obj_idx": a, "sub_idx": b, "relation": relation}


def tests():
    checks = []
    nodes = [entity(0), entity(1), entity(2, "table")]
    symmetric = [edge(0, 2), edge(1, 2)]
    h, _ = colors(nodes, symmetric)
    assert all(c[0] == c[1] for c in h)
    checks.append("Equal labeled neighborhoods remain indistinguishable.")
    h, _ = colors(nodes, [edge(0, 2), edge(2, 1)])
    assert h[0][0] == h[0][1] and h[1][0] != h[1][1]
    checks.append("Direction alone can distinguish equal noun features.")
    altered = [entity(0, attribute="red"), entity(1), entity(2, "table")]
    assert colors(altered, symmetric)[0][0][0] != colors(altered, symmetric)[0][0][1]
    checks.append("Observed attributes distinguish input states, not referents.")
    mapping = {0: 17, 1: 9, 2: 42}
    remapped_nodes = [dict(n, node_id=mapping[n["node_id"]]) for n in nodes]
    remapped_edges = [edge(mapping[e["obj_idx"]], mapping[e["sub_idx"]])
                      for e in symmetric]
    h2, _ = colors(remapped_nodes, remapped_edges)
    assert all(h[k][0] != h[k][1] for k in (1, 2))
    original, _ = colors(nodes, symmetric)
    assert all(original[k][n] == h2[k][mapping[n]]
               for k in range(3) for n in mapping)
    checks.append("Node renumbering preserves signatures; IDs are not features.")
    reordered, _ = colors(list(reversed(nodes)), list(reversed(symmetric)))
    assert original == reordered
    checks.append("Node and edge ordering do not change signatures.")
    _, missing = colors(nodes, symmetric + [edge(0, 99)])
    assert len(missing) == 1
    checks.append("Missing graph endpoints are counted, not silently invented.")
    isolated, _ = colors([entity(0), entity(1)], [])
    assert all(c[0] == c[1] for c in isolated)
    checks.append("Isolated identical mentions cannot acquire identity from depth.")
    return checks


def main():
    role_path = ROOT / "pipeline/reports/mention_role_objective_20260916.json"
    graph_path = ROOT / "pipeline/reports/entity_binding_20260916.json"
    roles = json.loads(role_path.read_text(encoding="utf-8"))["control_manifest"]
    graphs = {(r["scene"], r["ann_id"]): r for r in
              json.loads(graph_path.read_text(encoding="utf-8"))["rows"]}
    rows = []
    for mention in roles:
        key = (mention["scene"], mention["ann_id"])
        graph = graphs[key]
        history, missing = colors(graph["entities"], graph["edges"])
        node = mention["node_id"]
        peers = [[other for other, color in state.items()
                  if other != node and color == state[node]] for state in history]
        rows.append({
            **{k: mention[k] for k in ("scene", "ann_id", "node_id", "cue",
                                       "success", "confident_wrong")},
            "equal_signature_peers_by_round": peers,
            "target_node0_equal_by_round": [state[node] == state[0] for state in history],
            "incident_edges": [e for e in graph["edges"]
                               if node in (e["obj_idx"], e["sub_idx"])],
            "dangling_edges": missing,
        })
    result = {
        "scope": "Existing fixed TRAIN graph records only; no native replay.",
        "checks": tests(),
        "denominator": {"mentions": len(rows),
                        "expressions": len({(r["scene"], r["ann_id"]) for r in rows})},
        "summary": {
            "target_equal_by_round": [sum(r["target_node0_equal_by_round"][i]
                                        for r in rows) for i in range(3)],
            "any_peer_equal_by_round": [sum(bool(r["equal_signature_peers_by_round"][i])
                                          for r in rows) for i in range(3)],
            "mentions_without_incident_edge": sum(not r["incident_edges"] for r in rows),
            "mentions_in_graph_with_missing_endpoints": sum(bool(r["dangling_edges"])
                                                           for r in rows),
            "cue_counts": dict(Counter(r["cue"] for r in rows)),
        },
        "rows": rows,
        "derivation": [
            "c0(v)=(ordered noun tokens, sorted attribute strings).",
            "c[k+1](v)=(c[k](v), multiset(direction,relation,c[k](neighbor))).",
            "Any shared deterministic message function on these inputs gives equal "
            "states to nodes with equal recursive signatures, by induction.",
            "Unequal signatures are only availability of distinguishing input, "
            "not proof of correct roles, referents, predicate truth or useful gradients.",
            "Do not use target node flags, native target labels or node IDs as "
            "identifying features. Node0 is only a diagnostic comparison.",
            "A crossmodal mechanism would additionally require instance-indexed "
            "paired physical support. Text-graph distinction does not supply it.",
        ],
        "limitations": "Parser graph, not semantic truth; exact lexical strings "
        "do not capture synonymy. Missing endpoints excluded and reported. "
        "Generic graph refinement is a diagnostic, not a proposed novel model. "
        "No novelty, efficacy, resource or admission claim.",
        "sources": {str(p.relative_to(ROOT)).replace("\\", "/"):
                    hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (role_path, graph_path, Path(__file__))},
    }
    out = ROOT / "pipeline/reports/mention_graph_observability_20260916.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("checks", "denominator", "summary")},
                     indent=2))


if __name__ == "__main__":
    main()
