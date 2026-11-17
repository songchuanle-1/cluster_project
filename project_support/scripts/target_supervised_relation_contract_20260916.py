"""Static reference calculus, not a new mechanism or training admission."""
import hashlib
import json
import math
from pathlib import Path


def softmax(values):
    maximum = max(values)
    weights = [math.exp(v - maximum) for v in values]
    return [v / sum(weights) for v in weights]


def evaluate(unary, anchor, relation, target):
    joint = [[unary[i] + anchor[j] + relation[i][j]
              for j in range(len(anchor))] for i in range(len(unary))]
    flat = softmax([v for row in joint for v in row])
    p = [flat[i * len(anchor):(i + 1) * len(anchor)]
         for i in range(len(unary))]
    q = [sum(row) for row in p]
    posterior = [v / q[target] for v in p[target]]
    grad_r = [[p[i][j] - (posterior[j] if i == target else 0)
               for j in range(len(anchor))] for i in range(len(unary))]
    grad_a = [sum(p[i][j] for i in range(len(unary))) - posterior[j]
              for j in range(len(anchor))]
    return -math.log(q[target]), q, grad_a, grad_r


def main():
    root = Path(__file__).resolve().parents[1]
    u, a = [0.2, -0.3], [0.4, -0.2, 0.1]
    r = [[0.8, -0.6, 0.2], [-0.4, 0.9, -0.1]]
    loss, q, grad_a, grad_r = evaluate(u, a, r, 0)
    checks = []
    h = 1e-5
    errors = []
    for j in range(3):
        plus, minus = a.copy(), a.copy()
        plus[j] += h
        minus[j] -= h
        finite = (evaluate(u, plus, r, 0)[0] - evaluate(u, minus, r, 0)[0]) / (2*h)
        errors.append(abs(finite - grad_a[j]))
    for i in range(2):
        for j in range(3):
            plus, minus = [row.copy() for row in r], [row.copy() for row in r]
            plus[i][j] += h
            minus[i][j] -= h
            finite = (evaluate(u, a, plus, 0)[0] - evaluate(u, a, minus, 0)[0]) / (2*h)
            errors.append(abs(finite - grad_r[i][j]))
    assert max(errors) < 1e-8
    checks.append("Nine target-supervised partials agree with finite differences.")
    assert sum(abs(v) for v in grad_a) > 0.01
    checks.append("No anchor labels are needed for a nonzero anchor-logit gradient.")
    zero = [[0.0] * 3 for _ in range(2)]
    _, q_zero, a_zero, _ = evaluate(u, a, zero, 0)
    assert all(abs(x-y) < 1e-12 for x, y in zip(q_zero, softmax(u)))
    assert max(abs(v) for v in a_zero) < 1e-12
    checks.append("Without interaction, anchor probabilities cancel out of target likelihood.")
    separable = [[b + c for c in [0.3, -0.2, 0.7]] for b in [0.5, -0.1]]
    _, _, a_separable, _ = evaluate(u, a, separable, 0)
    assert max(abs(v) for v in a_separable) < 1e-12
    checks.append("Additively separable relation scores also give zero anchor gradient.")
    order = [2, 0, 1]
    permuted = evaluate(u, [a[j] for j in order], [[row[j] for j in order] for row in r], 0)
    assert abs(permuted[0] - loss) < 1e-12
    checks.append("Joint anchor permutation preserves the target likelihood.")
    shift = [0.7, -0.5, 0.2]
    gauge = evaluate(u, [x+y for x, y in zip(a, shift)],
                     [[v-shift[j] for j, v in enumerate(row)] for row in r], 0)
    assert abs(gauge[0] - loss) < 1e-12
    checks.append("Anchor unary/relation gauge prevents unique internal parameter identification.")
    contradictory = [[v if i == 0 else -v for v in row] for i, row in enumerate(r)]
    changed = evaluate(u, a, contradictory, 0)
    assert abs(changed[0] - loss) > 1e-3
    checks.append("A nonseparable relation change can change supervised target probability.")
    sources = [
        Path(__file__),
        root / "pipeline/reports/ns3d_original_20260916.html",
        root / "pipeline/reports/correspondence_identification_20260916.json",
    ]
    result = dict(
        scope="Synthetic static reference likelihood; no native data, model, "
              "optimizer, novelty or scientific-admission evidence.",
        equations=dict(
            joint="p(i,j)=softmax_over_pairs(u_i+a_j+R_ij)",
            output="q_i=sum_j p(i,j)",
            objective="L=-log q_target",
            relation_gradient="p(i,j)-1[i=target]*p(j|target)",
            anchor_gradient="p(j)-p(j|target)",
            cost="O(Q*K) scalar relation scores; no superpoint NxN attention"),
        checks=checks, checks_passed=len(checks), finite_difference_max_error=max(errors),
        example=dict(loss=loss, target_marginal=q, anchor_gradient=grad_a),
        conclusion="Lack of direct auxiliary-anchor labels is not a universal "
                   "no-learning theorem. Nonzero gradient is not correct-anchor "
                   "identification or causal efficacy. Generic target-supervised "
                   "latent relations are prior art and not a proposed new variant.",
        sources={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sources},
    )
    path = root / "pipeline/reports/target_supervised_relation_contract_20260916.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
