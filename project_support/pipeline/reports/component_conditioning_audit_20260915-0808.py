"""Offline exact-enumeration checks; no production imports or training."""
import itertools
import json
import math
from pathlib import Path


def conditional(z, y, groups):
    loss = 0.0
    grad = [0.0] * len(z)
    for group in groups:
        states = list(itertools.combinations(group, sum(y[i] for i in group)))
        scores = [sum(z[i] for i in state) for state in states]
        maximum = max(scores)
        weights = [math.exp(s - maximum) for s in scores]
        total = sum(weights)
        loss += maximum + math.log(total) - sum(z[i] * y[i] for i in group)
        for i in group:
            grad[i] = (sum(w for s, w in zip(states, weights) if i in s)
                       / total - y[i]) / len(z)
    return loss / len(z), grad


def main():
    groups = [(0, 1), (2, 3)]
    global_group = [(0, 1, 2, 3)]
    cases = 0
    max_error = 0.0
    for y in itertools.product((0, 1), repeat=4):
        for z in ((-4., -4., 4., 4.), (-1., 2., 3., -2.), (0.,) * 4):
            value, grad = conditional(z, y, groups)
            shifted = [z[0] + 7, z[1] + 7, z[2] - 3, z[3] - 3]
            shifted_value, shifted_grad = conditional(shifted, y, groups)
            assert abs(value - shifted_value) < 1e-12
            assert max(abs(a - b) for a, b in zip(grad, shifted_grad)) < 1e-12
            # Direct Bernoulli conditioning is an independent value reference.
            probabilities = [1 / (1 + math.exp(-v)) for v in z]
            numerator = math.prod(p if t else 1 - p for p, t in zip(probabilities, y))
            denominator = 0.0
            for state in itertools.product((0, 1), repeat=4):
                if all(sum(state[i] for i in g) == sum(y[i] for i in g)
                       for g in groups):
                    denominator += math.prod(p if t else 1 - p
                                             for p, t in zip(probabilities, state))
            assert abs(value + math.log(numerator / denominator) / 4) < 1e-12
            for i in range(4):
                plus, minus = list(z), list(z)
                plus[i] += 1e-5
                minus[i] -= 1e-5
                finite = (conditional(plus, y, groups)[0]
                          - conditional(minus, y, groups)[0]) / 2e-5
                error = abs(finite - grad[i])
                max_error = max(max_error, error)
                assert error < 1e-8
            # A sole component has precisely the full-group conditional law.
            assert conditional(z, y, global_group) == conditional(z, y, [tuple(range(4))])
            cases += 1
    z, y = [-4., -4., 4., 4.], [1, 1, 0, 0]
    local_loss, local_grad = conditional(z, y, groups)
    global_loss, global_grad = conditional(z, y, global_group)
    assert local_loss == 0 and local_grad == [0.] * 4
    assert global_grad[0] < 0 and global_grad[1] < 0
    assert global_grad[2] > 0 and global_grad[3] > 0
    result = {
        "status": "PASS", "label_logit_cases": cases,
        "finite_difference_coordinates": cases * 4,
        "max_gradient_error": max_error,
        "counterexample": {"z": z, "y": y, "component_loss": local_loss,
                           "component_gradient": local_grad,
                           "global_loss": global_loss, "global_gradient": global_grad},
        "scope": "Synthetic full-induced-contact-component audit; not full-loss or native efficacy",
    }
    Path(__file__).with_suffix(".json").write_text(json.dumps(result, indent=2) + "\n",
                                                encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
