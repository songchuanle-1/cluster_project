"""Pure mathematical controls for proposed latent role likelihoods."""
import hashlib
import json
import math
from pathlib import Path


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def independent_unknown_loss(xs):
    return -sum(math.log(sigmoid(x) + sigmoid(-x)) for x in xs)


def shared_unknown_loss(xs):
    p_same = math.prod(sigmoid(x) for x in xs)
    p_other = math.prod(sigmoid(-x) for x in xs)
    return -math.log(p_same + p_other)


def finite_gradient(fn, xs, h=1e-5):
    result = []
    for i in range(len(xs)):
        plus, minus = list(xs), list(xs)
        plus[i] += h
        minus[i] -= h
        result.append((fn(plus)-fn(minus))/(2*h))
    return result


rows = []
for xs in ([0.0], [-2.0], [2.0], [2.0, 2.0], [-2.0, -2.0], [2.0, -2.0]):
    rows.append(dict(logits=xs, independent_loss=independent_unknown_loss(xs),
        independent_gradient=finite_gradient(independent_unknown_loss, xs),
        shared_loss=shared_unknown_loss(xs),
        shared_gradient=finite_gradient(shared_unknown_loss, xs)))
assert all(abs(r["independent_loss"]) < 1e-12 for r in rows)
assert all(max(map(abs, r["independent_gradient"])) < 1e-8 for r in rows)
assert abs(shared_unknown_loss([2.0])-shared_unknown_loss([-2.0])) < 1e-12
assert abs(shared_unknown_loss([2.0, 2.0])-shared_unknown_loss([-2.0, -2.0])) < 1e-12
assert shared_unknown_loss([2.0, 2.0]) < shared_unknown_loss([0.0, 0.0])
assert shared_unknown_loss([-2.0, -2.0]) < shared_unknown_loss([0.0, 0.0])
# Repeated same-lemma mentions of DIFFERENT objects are a valid counterexample.
# No evidence distinguishing the two worlds is present in either likelihood.
assert shared_unknown_loss([2.0, 2.0]) < shared_unknown_loss([2.0, -2.0])
output = dict(controls="PASS", rows=rows,
    conclusions=[
        "Independent binary role marginal with both labels allowed equals zero loss.",
        "Shared binary role encourages agreement,not correct semantic identity.",
        "Sign symmetry leaves same-target and different-object worlds unidentifiable.",
        "Known target anchoring removes sign symmetry only if coreference is valid; "
        "same lemma does not license anchoring.",
        "Reject these bare likelihoods as standalone grounding mechanisms; "
        "need independent discriminating observations or justified constraints."],
    scope="Synthetic algebra only;not native efficacy or a new partial-label algorithm.",
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
path = Path(__file__).resolve().parents[1] / "pipeline/reports/role_latent_degeneracy_20260916.json"
path.write_text(json.dumps(output, indent=2))
print(json.dumps(output, indent=2))
