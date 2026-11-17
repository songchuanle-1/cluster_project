"""Static counterexample: target-only training need not identify anchor outputs."""
import hashlib
import json
import math
from pathlib import Path


def distribution(u, v, role):
    logits = [a + role*b for a, b in zip(u, v)]
    weights = [math.exp(x-max(logits)) for x in logits]
    return [x/sum(weights) for x in weights]


def loss(u, v, role, label):
    return -math.log(distribution(u, v, role)[label])


def main():
    u = [2., -2.]
    alternatives = ([0., 0.], [-8., 8.])
    targets = [distribution(u, v, 0) for v in alternatives]
    anchors = [distribution(u, v, 1) for v in alternatives]
    assert targets[0] == targets[1]
    assert anchors[0][0] > .98 and anchors[1][1] > .99999
    eps = 1e-5
    gradients = []
    for v in alternatives:
        gradient = []
        for i in range(2):
            plus, minus = list(v), list(v)
            plus[i] += eps
            minus[i] -= eps
            gradient.append((loss(u, plus, 0, 0)-loss(u, minus, 0, 0))/(2*eps))
        gradients.append(gradient)
    assert all(g == 0 for gradient in gradients for g in gradient)
    # Identification contrast: an actual labeled anchor observation distinguishes
    # these functions; this is a synthetic control, not permission to add labels.
    anchor_losses = [loss(u, v, 1, 1) for v in alternatives]
    assert anchor_losses[0] > 4 and anchor_losses[1] < 1e-5
    result = dict(
        target_distributions=targets, anchor_distributions=anchors,
        target_only_v_gradients=gradients, labeled_anchor_control_losses=anchor_losses,
        formula="p(i|u,v,r)=softmax_i(u+r*v); observed target contexts r=0; anchor r=1",
        conclusion="Shared parameters alone do not guarantee target-to-anchor identification.",
        limitations="Existence counterexample, not proof native model uses this shortcut, "
        "not impossibility of transfer, and not an admission requirement for extra labels. "
        "r is a context distinction representable by contextual embeddings, not new "
        "metadata proposed for inference. Does not repeat latent binary-role mixtures.",
        sources={str(Path(__file__)): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    )
    out = Path(__file__).resolve().parents[1]/"pipeline/reports/target_anchor_transfer_20260916.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
