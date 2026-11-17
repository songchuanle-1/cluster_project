"""Synthetic SCM-only gradient falsifier; no population or full-loss claim."""
import json

import numpy as np

from scm_math_check_20260914 import objective


def main():
    xyz = np.array([[0., 0, 0], [1., 0, 0], [2., 0, 0]])
    target = np.array([1., 0, 0])
    probabilities = np.array([[.49, .51, .001], [.51, .49, .49]])
    logits = np.log(probabilities) - np.log1p(-probabilities)
    scores = np.zeros(2)
    hard = probabilities > .5
    iou = (hard & target.astype(bool)).sum(1) / (
        hard | target.astype(bool)
    ).sum(1)
    costs = [
        objective(logits[q:q + 1], np.zeros(1), xyz, target)[0]
        for q in range(2)
    ]
    loss, _, gradient = objective(logits, scores, xyz, target)
    finite = np.empty(2)
    for q in range(2):
        offset = np.zeros(2)
        offset[q] = 1e-6
        finite[q] = (
            objective(logits, scores + offset, xyz, target)[0]
            - objective(logits, scores - offset, xyz, target)[0]
        ) / 2e-6
    stepped = scores - gradient
    after = objective(logits, stepped, xyz, target)[0]
    swapped = objective(logits[::-1], scores[::-1], xyz, target)
    assert iou.tolist() == [0., 1.]
    assert 0 < costs[0] < costs[1]
    assert gradient[0] < 0 < gradient[1]
    assert np.max(np.abs(gradient - finite)) < 1e-8
    assert np.isclose(swapped[0], loss)
    assert np.allclose(swapped[2][::-1], gradient)
    assert after < loss and np.argmax(stepped) == 0
    print(json.dumps({
        "status": "PASS_SYNTHETIC_COUNTEREXAMPLE",
        "fixtures": 1,
        "queries": 2,
        "superpoints": 3,
        "hard_iou": iou.tolist(),
        "individual_transport": costs,
        "selector_gradient": gradient.tolist(),
        "finite_difference_max_error": float(np.max(np.abs(gradient - finite))),
        "loss_before": float(loss),
        "loss_after_selector_step": float(after),
        "selected_after_step": int(np.argmax(stepped)),
        "scope": "SCM-only reference; not full loss, production execution or dataset prevalence",
    }, indent=2))


if __name__ == "__main__":
    main()
