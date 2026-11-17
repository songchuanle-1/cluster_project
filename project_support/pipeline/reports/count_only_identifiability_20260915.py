"""Synthetic count-only audit. No model, data, queue or GPU access."""
import itertools
import json
import math


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def evaluate(z, k):
    n = len(z)
    subsets = list(itertools.combinations(range(n), k))
    scores = [sum(z[i] for i in subset) for subset in subsets]
    top = max(scores)
    weights = [math.exp(score - top) for score in scores]
    total = sum(weights)
    log_z = top + math.log(total)
    q = [sum(w for s, w in zip(subsets, weights) if i in s) / total
         for i in range(n)]
    partition = sum(max(v, 0) + math.log1p(math.exp(-abs(v))) for v in z)
    return (partition - log_z) / n, [(sigmoid(v) - qi) / n
                                    for v, qi in zip(z, q)]


def main():
    cases, error = 0, 0.0
    for n in range(1, 8):
        for k in range(n + 1):
            for shift in (-20.0, 0.0, 20.0):
                z = [(i - n / 2) * 1.7 + shift for i in range(n)]
                _, grad = evaluate(z, k)
                for i in range(n):
                    plus, minus = z.copy(), z.copy()
                    plus[i] += 1e-4
                    minus[i] -= 1e-4
                    fd = (evaluate(plus, k)[0] - evaluate(minus, k)[0]) / 2e-4
                    error = max(error, abs(fd - grad[i]))
                cases += 1
    wrong, correct = [0, 1], [1, 0]
    z = [4.0, -4.0]
    loss, grad = evaluate(z, sum(wrong))
    assert (loss, grad) == evaluate(z, sum(correct))
    assert grad[0] < 0 < grad[1]
    updated = [v - g for v, g in zip(z, grad)]
    after, _ = evaluate(updated, 1)
    assert after < loss and updated[0] - updated[1] > z[0] - z[1]
    assert evaluate([0.0, 0.0], 1)[1] == [0.0, 0.0]
    assert error < 1e-7
    print(json.dumps({
        "status": "PASS", "gradient_cases": cases, "max_gradient_error": error,
        "counterexample_logits": z, "wrong_target": wrong, "gradient": grad,
        "count_loss_before": loss, "count_loss_after_unit_descent": after,
        "wrong_margin_before": z[0] - z[1],
        "wrong_margin_after": updated[0] - updated[1],
        "label_permutation_invariant": True, "symmetric_stationary": True,
        "scope": "Synthetic counterexample; no efficacy or novelty claim"
    }, indent=2))


if __name__ == "__main__":
    main()
