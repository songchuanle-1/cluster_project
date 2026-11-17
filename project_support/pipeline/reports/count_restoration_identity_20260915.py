"""Offline enumeration audit; does not load data or modify training state."""
import itertools
import json
import math


def logsumexp(values):
    top = max(values)
    return top + math.log(sum(math.exp(v - top) for v in values))


def softplus(x):
    return max(x, 0) + math.log1p(math.exp(-abs(x)))


def losses(z, y):
    n, k = len(y), sum(y)
    log_z = logsumexp([
        sum(z[i] for i in chosen)
        for chosen in itertools.combinations(range(n), k)
    ])
    dot = sum(a * b for a, b in zip(z, y))
    partition = sum(map(softplus, z))
    return (log_z - dot) / n, (partition - log_z) / n, (partition - dot) / n


def main():
    count = 0
    max_value_error = max_gradient_error = max_shift_error = 0.0
    for n in range(1, 8):
        for y in itertools.product((0, 1), repeat=n):
            for shift in (-50.0, 0.0, 50.0):
                z = [(i - n / 2) * 1.7 + shift for i in range(n)]
                a, c, b = losses(z, y)
                max_value_error = max(max_value_error, abs(a + c - b))
                shifted_a = losses([v + 3 for v in z], y)[0]
                max_shift_error = max(max_shift_error, abs(a - shifted_a))
                for i in range(n):
                    plus, minus = z.copy(), z.copy()
                    plus[i] += 1e-4
                    minus[i] -= 1e-4
                    ap, cp, _ = losses(plus, y)
                    am, cm, _ = losses(minus, y)
                    observed = (ap + cp - am - cm) / 2e-4
                    expected = (1 / (1 + math.exp(-z[i])) - y[i]) / n
                    max_gradient_error = max(max_gradient_error, abs(observed - expected))
                count += 1
    assert max_value_error < 1e-10
    assert max_gradient_error < 1e-7
    assert max_shift_error < 1e-10
    print(json.dumps(dict(
        cases=count, max_value_error=max_value_error,
        max_gradient_error=max_gradient_error, max_shift_error=max_shift_error,
        status="PASS", scope="synthetic algebra; no efficacy or novelty claim"
    ), indent=2))


if __name__ == "__main__":
    main()
