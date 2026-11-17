"""Reference checks for the proposed SCM loss, not production training code."""
import numpy as np


def objective(mask_logits, score_logits, xyz, target):
    logm = -np.logaddexp(0, -mask_logits)
    b = np.exp(logm - np.logaddexp.reduce(logm, axis=1)[:, None])
    loga = -np.logaddexp(0, -score_logits)
    alpha = np.exp(loga - np.logaddexp.reduce(loga))
    p = alpha @ b
    t = target / target.sum()
    diameter = np.linalg.norm(np.ptp(xyz, axis=0))
    g = np.zeros(len(p))
    value = 0.0
    for axis in range(3):
        order = np.argsort(xyz[:, axis], kind="stable")
        gaps = np.diff(xyz[order, axis]) / diameter
        cdf = np.cumsum((p - t)[order])[:-1]
        value += np.dot(gaps, np.abs(cdf)) / 3
        ordered_grad = np.r_[np.cumsum((gaps * np.sign(cdf))[::-1])[::-1], 0]
        g[order] += ordered_grad / 3
    h = b @ g
    sigmoid_d = np.exp(loga)
    dd = alpha * (h - alpha @ h) * (1 - sigmoid_d)
    dm = alpha[:, None] * b * (1 - np.exp(logm)) * (g - h[:, None])
    return value, dm, dd


def main():
    rng = np.random.default_rng(1999)
    xyz = rng.normal(size=(9, 3))
    masks = rng.normal(size=(4, 9))
    scores = rng.normal(size=4)
    target = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0.])
    val, dm, dd = objective(masks, scores, xyz, target)
    worst = 0
    for array, expected in ((masks, dm), (scores, dd)):
        for index in np.ndindex(array.shape):
            original = array[index]
            array[index] = original + 1e-6
            plus = objective(masks, scores, xyz, target)[0]
            array[index] = original - 1e-6
            minus = objective(masks, scores, xyz, target)[0]
            array[index] = original
            worst = max(worst, abs((plus - minus) / 2e-6 - expected[index]))
    assert worst < 1e-7, worst
    perm = rng.permutation(len(xyz))
    assert np.isclose(val, objective(masks[:, perm], scores, xyz[perm], target[perm])[0])
    assert np.isclose(val, objective(masks, scores, xyz * 7 + 12, target)[0])
    assert np.isclose(val, objective(masks, scores, -xyz[:, [2, 0, 1]], target)[0])
    identical = np.tile(masks[0], (4, 1))
    assert np.max(np.abs(objective(identical, scores, xyz, target)[2])) < 1e-14
    assert np.isfinite(objective(masks - 1000, scores - 1000, xyz, target)[0])
    # Distinct diagonal supports have identical coordinate marginals.
    square = np.array([[0., 0, 0], [1, 1, 0], [0, 1, 0], [1, 0, 0]])
    diagonal_mask = np.array([[80., 80., -80., -80.]])
    other_diagonal = np.array([0., 0., 1., 1.])
    blind = objective(diagonal_mask, np.array([0.]), square, other_diagonal)[0]
    assert abs(blind) < 1e-14
    # Same-size disjoint predictions; farther displacement has larger cost.
    line = np.array([[0., 0, 0], [1, 0, 0], [2, 0, 0]])
    near = objective(np.array([[-80., 80, -80]]), np.array([0.]), line, np.array([1., 0, 0]))[0]
    far = objective(np.array([[-80., -80, 80]]), np.array([0.]), line, np.array([1., 0, 0]))[0]
    assert np.isclose(far, 2 * near)
    print(f"PASS: finite differences max_abs_error={worst:.3e}")
    print("PASS: SP permutation, translation/scale, axis reflection/permutation")
    print("PASS: identical-mask selector gradient zero; extreme-negative logits finite")
    print(f"PASS: documented marginal blind spot={blind:.3e}; near={near:.6f}, far={far:.6f}")
    print("NOT RUN: production torch/AMP, data batches, resource benchmark, training")


if __name__ == "__main__":
    main()
