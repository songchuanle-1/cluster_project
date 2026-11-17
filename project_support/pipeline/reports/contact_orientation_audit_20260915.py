"""CPU falsifier for unsigned contact-edge target-orientation claims."""
import itertools
import json
import math


def objective(z, y, edges):
    p = [1 / (1 + math.exp(-v)) for v in z]
    g = [0.0] * len(z)
    loss = 0.0
    for i, j in edges:
        d = abs(y[i] - y[j])
        r = p[i] * (1 - p[j]) + (1 - p[i]) * p[j]
        loss -= d * math.log(r) + (1 - d) * math.log1p(-r)
        factor = (r - d) / (r * (1 - r))
        g[i] += factor * (1 - 2 * p[j]) * p[i] * (1 - p[i])
        g[j] += factor * (1 - 2 * p[i]) * p[j] * (1 - p[j])
    scale = max(1, len(edges))
    return loss / scale, [v / scale for v in g]


def main():
    cases, max_error = 0, 0.0
    for n in range(2, 7):
        z = [(-1) ** i * (i + 1) / 3 for i in range(n)]
        edges = list(zip(range(n - 1), range(1, n)))
        for y in itertools.product((0, 1), repeat=n):
            loss, grad = objective(z, y, edges)
            assert abs(loss - objective(z, [1 - v for v in y], edges)[0]) < 1e-12
            assert abs(loss - objective([-v for v in z], y, edges)[0]) < 1e-12
            for i, actual in enumerate(grad):
                a, b = z.copy(), z.copy()
                a[i] += 1e-5
                b[i] -= 1e-5
                fd = (objective(a, y, edges)[0] - objective(b, y, edges)[0]) / 2e-5
                max_error = max(max_error, abs(actual - fd))
            cases += 1
    assert max_error < 1e-8
    z, y, edges = [4.0, -4.0], [0, 1], [(0, 1)]
    before, grad = objective(z, y, edges)
    after_z = [v - g for v, g in zip(z, grad)]
    after = objective(after_z, y, edges)[0]
    assert after < before and after_z[0] - after_z[1] > 8
    assert objective([0, 0], y, edges)[1] == [0, 0]
    dz, dy, de = [1, -2, 3, -1, 2], [1, 0, 0, 1, 1], [(0, 1), (2, 3)]
    base, gg = objective(dz, dy, de)
    assert gg[4] == 0
    assert abs(base - objective([-1, 2, 3, -1, 2], dy, de)[0]) < 1e-12
    assert objective(dz, [0, 1, 0, 1, 1], de) == (base, gg)
    assert objective(dz, dy, []) == (0, [0] * 5)
    print(json.dumps({
        "status": "PASS", "binary_label_cases": cases,
        "max_gradient_error": max_error,
        "wrong_orientation": {"loss_before": before, "loss_after": after,
                              "wrong_margin_before": 8, "wrong_margin_after": after_z[0] - after_z[1]},
        "component_complement_and_isolation": "PASS",
        "zero_logit_stationarity": "PASS",
        "scope": "synthetic falsifier only; no native TRAIN or efficacy result"
    }, indent=2))


if __name__ == "__main__":
    main()
