"""Exhaustively check the graph domain of the 0808 rejection argument."""
import hashlib
import itertools
import json
from pathlib import Path


def components(vertices, edges):
    adjacency = {v: set() for v in vertices}
    for a, b in edges:
        adjacency[a].add(b)
        adjacency[b].add(a)
    unseen = set(vertices)
    result = []
    while unseen:
        root = unseen.pop()
        part, todo = {root}, [root]
        while todo:
            for neighbor in adjacency[todo.pop()] & unseen:
                unseen.remove(neighbor)
                part.add(neighbor)
                todo.append(neighbor)
        result.append(part)
    return result


def check(edges, labels):
    crossing = [(a, b) for a, b in edges if labels[a] != labels[b]]
    boundary = {v for edge in crossing for v in edge}
    induced = [(a, b) for a, b in edges if a in boundary and b in boundary]
    counts = []
    for graph in (crossing, induced):
        groups = components(boundary, graph)
        for group in groups:
            assert 0 < sum(labels[i] for i in group) < len(group)
        counts.append(len(groups))
    return boundary, counts


def main():
    cases = nonempty = 0
    component_counts = [0, 0]
    by_n = {}
    for n in range(1, 6):
        possible = list(itertools.combinations(range(n), 2))
        count = 0
        for mask in range(1 << len(possible)):
            edges = [e for i, e in enumerate(possible) if mask & (1 << i)]
            for labels in itertools.product((0, 1), repeat=n):
                boundary, counts = check(edges, labels)
                cases += 1
                count += 1
                nonempty += bool(boundary)
                component_counts = [a + b for a, b in zip(component_counts, counts)]
        by_n[str(n)] = count
    old_boundary, _ = check([(0, 1), (2, 3)], (1, 1, 0, 0))
    assert not old_boundary
    mixed_boundary, mixed_counts = check([(0, 1), (2, 3)], (1, 0, 1, 0))
    assert len(mixed_boundary) == 4 and mixed_counts == [2, 2]
    source = Path(__file__).resolve().parents[2] / (
        "Cluster/framework/model/Quard_model/"
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bca/"
        "boundary_assignment.py"
    )
    result = dict(
        status="PASS", graph_label_cases=cases, cases_by_n=by_n,
        nonempty_boundary_cases=nonempty,
        crossing_components_checked=component_counts[0],
        induced_components_checked=component_counts[1],
        homogeneous_boundary_components=0,
        old_counterexample_boundary_size=len(old_boundary),
        mixed_control_components=mixed_counts,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope="Synthetic exhaustive graph audit; no native prevalence or efficacy",
    )
    output = Path(__file__).with_suffix(".json")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
