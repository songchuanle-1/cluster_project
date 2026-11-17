"""Bounded archived-graph and finite factor controls; no native model execution."""
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def marginal(unary, factors):
    states = np.array(list(itertools.product(range(unary.shape[1]),
                                            repeat=len(unary))))
    score = sum(unary[k, states[:, k]] for k in range(len(unary)))
    for a, b, matrix in factors:
        score += matrix[states[:, a], states[:, b]]
    prob = np.exp(score - score.max())
    prob /= prob.sum()
    return np.bincount(states[:, 0], weights=prob, minlength=unary.shape[1])


def controls():
    # r=target, o=other chair, a=table: the short-side predicate belongs to o.
    u = np.array([[0.0, 0.0], [0.3, -0.2], [1.1, -0.4]])
    distinct = np.array([[-3.0, 0.0], [0.0, -3.0]])
    boundary = np.array([[2.0, -1.0], [-2.0, 1.0]])
    owned = marginal(u, [(0, 1, distinct), (1, 2, boundary)])
    flattened = marginal(u, [(0, 1, distinct), (0, 2, boundary)])
    assert owned.argmax() != flattened.argmax()
    eps = 1e-5
    def gradient(edges):
        plus, minus = boundary.copy(), boundary.copy()
        plus[0, 0] += eps
        minus[0, 0] -= eps
        return (-np.log(marginal(u, edges(plus))[1])
                + np.log(marginal(u, edges(minus))[1])) / (2 * eps)
    linked = gradient(lambda b: [(0, 1, distinct), (1, 2, b)])
    disconnected = gradient(lambda b: [(1, 2, b)])
    assert abs(linked) > 1e-3 and abs(disconnected) < 1e-9
    perm = [1, 0]
    permuted = marginal(u[:, perm], [
        (0, 1, distinct[np.ix_(perm, perm)]),
        (1, 2, boundary[np.ix_(perm, perm)])])
    assert np.allclose(permuted, owned[perm])
    # Exact chain elimination must agree with enumeration.
    message = np.exp(u[2][None, :] + boundary).sum(axis=1)
    target = np.exp(u[0]) * (
        np.exp(distinct + u[1][None, :]) * message[None, :]).sum(axis=1)
    target /= target.sum()
    assert np.allclose(target, owned)
    repeated_u = np.array([[2., 0.], [2., 0.]])
    free = marginal(repeated_u, [])
    excluded = marginal(repeated_u, [(0, 1, distinct)])
    assert excluded[0] < free[0]
    return {
        "checks_passed": 6,
        "owned_target_probability": owned.tolist(),
        "flattened_target_probability": flattened.tolist(),
        "linked_boundary_gradient": float(linked),
        "disconnected_boundary_gradient": float(disconnected),
        "checks": ["ownership relocation changes winner",
                   "indirect owned predicate has target-loss gradient",
                   "disconnected predicate cancels from target marginal",
                   "instance permutation equivariance",
                   "chain elimination equals exhaustive enumeration",
                   "universal distinctness distorts a repeated-referent control"],
        "scope": "Synthetic finite potentials, not learned/native scores or efficacy.",
    }


def main():
    paths = [ROOT / "pipeline/reports/mention_role_objective_20260916.json",
             ROOT / "pipeline/reports/entity_binding_20260916.json"]
    roles = json.loads(paths[0].read_text(encoding="utf-8"))["control_manifest"]
    graphs = {(r["scene"], r["ann_id"]): r for r in
              json.loads(paths[1].read_text(encoding="utf-8"))["rows"]}
    rows = []
    for role in roles:
        g = graphs[role["scene"], role["ann_id"]]
        nodes = {e["node_id"] for e in g["entities"]}
        adjacency = {n: set() for n in nodes}
        missing = []
        for e in g["edges"]:
            a, b = e["obj_idx"], e["sub_idx"]
            if a not in nodes or b not in nodes:
                missing.append(e)
                continue
            adjacency[a].add(b)
            adjacency[b].add(a)
        distance = {0: 0} if 0 in nodes else {}
        frontier = list(distance)
        while frontier:
            a = frontier.pop(0)
            for b in adjacency[a]:
                if b not in distance:
                    distance[b] = distance[a] + 1
                    frontier.append(b)
        rows.append({k: role[k] for k in
                     ("scene", "ann_id", "node_id", "cue", "success", "confident_wrong")})
        rows[-1].update(distance_to_target=distance.get(role["node_id"]),
                        missing_endpoints=missing)
    summary = {
        "mentions": len(rows),
        "expressions": len({(r["scene"], r["ann_id"]) for r in rows}),
        "scenes": len({r["scene"] for r in rows}),
        "connected_mentions": sum(r["distance_to_target"] is not None for r in rows),
        "indirect_mentions": sum((r["distance_to_target"] or 0) > 1 for r in rows),
        "disconnected_mentions": sum(r["distance_to_target"] is None for r in rows),
        "explicit_other": [r for r in rows if r["cue"] == "explicit_other_cue"],
    }
    result = {
        "scope": "Existing TRAIN parser graphs only; no new annotations or GPU work.",
        "summary": summary, "rows": rows, "controls": controls(),
        "derivation": [
            "E(z)=sum_v U_v(z_v)+sum_(v,w) R_vw(z_v,z_w).",
            "q(i)=sum_(z:z0=i) exp(E(z))/sum_z exp(E(z)); L=-log q(y).",
            "A disconnected component contributes an identical partition factor to every i and cancels.",
            "For chain 0-1-2, m21(j)=sum_k exp(U2(k)+R12(j,k)); "
            "q(i) proportional exp(U0(i))*sum_j exp(U1(j)+R01(i,j))*m21(j).",
            "This costs O(K^2) for this chain, not O(K^3); general loops need "
            "treewidth-dependent elimination and are not covered by that bound.",
            "Directed predicates retain their endpoint order even though connectivity is undirected.",
        ],
        "disposition": "Reference computation only: JVGN prior art, no novelty/admission.",
        "next_control": "For any future distinct mechanism compare owned endpoint, "
        "endpoint-relocated, and predicate-disabled branches with identical learned "
        "parameters and physical support. Freeze case manifest before native replay.",
        "limitations": [
            "Graph connectivity is input availability, not correct semantics or native causal attribution.",
            "No generic edges, equality or distinctness labels may be invented to connect components.",
            "Paired modalities do not fix ownership or physical index provenance.",
            "No complete native forward/backward, full resource result or improvement claim.",
        ],
        "sources": {str(p.relative_to(ROOT)).replace("\\", "/"):
                    hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in paths + [Path(__file__)]},
    }
    output = ROOT / "pipeline/reports/ownership_path_contract_20260916.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": summary, "controls": result["controls"]}, indent=2))


if __name__ == "__main__":
    main()
