"""Offline identity audit; no production imports, data access or training."""
import itertools
import json
import math
from pathlib import Path


def lse(values):
    peak = max(values)
    return peak + math.log(sum(math.exp(x - peak) for x in values))


def softplus(x):
    return max(x, 0.0) + math.log1p(math.exp(-abs(x)))


def sigmoid(x):
    return math.exp(-softplus(-x))


def pair(z, target):
    return softplus(z[1 - target] - z[target])


def main():
    errors = {"value": 0.0, "probability": 0.0, "gradient": 0.0, "shift": 0.0}
    cases = 0
    grid = (-12., -4., -1., 0., 1., 4., 12.)
    for a, b, target in itertools.product(grid, grid, (0, 1)):
        z = [a, b]
        bca_unnormalized = lse(z) - z[target]
        value = pair(z, target)
        errors["value"] = max(errors["value"], abs(value - bca_unnormalized))
        p = [sigmoid(x) for x in z]
        q = p[0] * (1 - p[1]) / (p[0] * (1 - p[1]) + (1 - p[0]) * p[1])
        errors["probability"] = max(errors["probability"], abs(q - sigmoid(a - b)))
        grad0 = sigmoid(a - b) - int(target == 0)
        for i, expected in enumerate((grad0, -grad0)):
            plus, minus = z.copy(), z.copy()
            plus[i] += 1e-5
            minus[i] -= 1e-5
            numerical = (pair(plus, target) - pair(minus, target)) / 2e-5
            errors["gradient"] = max(errors["gradient"], abs(numerical - expected))
        shifted = pair([a + 100., b + 100.], target)
        errors["shift"] = max(errors["shift"], abs(shifted - value))
        cases += 1
    reversed_z = [-4., 4.]
    g = sigmoid(-8.) - 1
    updated = [reversed_z[0] - g, reversed_z[1] + g]
    wrong_margin_before = reversed_z[1] - reversed_z[0]
    wrong_margin_after = updated[1] - updated[0]
    group_differences = []
    for z in ([0., 0., 0.], [2., 0., -1.]):
        edge_sum = softplus(z[1] - z[0]) + softplus(z[2] - z[0])
        group_loss = lse(z) - z[0]
        group_differences.append({"logits": z, "pair_sum": edge_sum,
                                  "group_bca_unnormalized": group_loss,
                                  "difference": edge_sum - group_loss})
    assert cases == 98
    assert max(errors.values()) < 1e-8, errors
    assert wrong_margin_after < wrong_margin_before
    assert pair(updated, 0) < pair(reversed_z, 0)
    assert abs(group_differences[0]["difference"] - group_differences[1]["difference"]) > .1
    result = {"status": "PASS", "pair_cases": cases, "max_errors": errors,
              "wrong_margin_before": wrong_margin_before,
              "wrong_margin_after": wrong_margin_after,
              "group_non_equivalence": group_differences,
              "scope": "synthetic CPU algebra only; no efficacy or resource admission"}
    output = Path(__file__).with_suffix(".json")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
