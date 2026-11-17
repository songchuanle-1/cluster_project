"""Exact rational counterexamples for proposed target displacement constraints."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sqnorm(a):
    return sum(x * x for x in a)


def audit():
    centers = [(F(0), F(0)), (F(2), F(1)), (F(-1), F(3))]
    targets = [(F(0), F(0)), (F(17), F(-9))]
    fields = [[sub(c, target) for c in centers] for target in targets]
    differences = [[sub(v[i], v[j]) for i in range(3) for j in range(3)] for v in fields]
    assert differences[0] == differences[1]
    for field in fields:
        cycle = add(add(sub(field[0], field[1]), sub(field[1], field[2])),
                    sub(field[2], field[0]))
        assert cycle == (0, 0)
    # Even a non-target-consistent field has zero exact-difference circulation.
    arbitrary = [(F(7), F(11)), (F(-4), F(6)), (F(8), F(-3))]
    cycle = add(add(sub(arbitrary[0], arbitrary[1]), sub(arbitrary[1], arbitrary[2])),
                sub(arbitrary[2], arbitrary[0]))
    assert cycle == (0, 0)
    votes = [sub(c, offset) for c, offset in zip(centers, arbitrary)]
    mean = tuple(sum(v[k] for v in votes) / len(votes) for k in range(2))
    pair = sum(sqnorm(sub(a, b)) for a in votes for b in votes) / len(votes) ** 2
    variance = 2 * sum(sqnorm(sub(v, mean)) for v in votes) / len(votes)
    assert pair == variance
    # Consensus has a continuum of incorrect-target zero-loss solutions.
    for target, field in zip(targets, fields):
        predicted = [sub(c, v) for c, v in zip(centers, field)]
        assert all(p == target for p in predicted)
        assert sum(sqnorm(sub(a, b)) for a in predicted for b in predicted) == 0
    return dict(
        exact_rational=True,
        target_independent_pair_differences=True,
        arbitrary_field_difference_cycle_zero=True,
        pairwise_vote_consistency_equals_twice_variance=True,
        two_distinct_target_zero_consensus_solutions=True,
        pair_loss=str(pair),
        disposition="Bare offset head overlaps AsphaltNet Eq5. Exact-difference cycle "
                    "and vote-consensus alone cannot distinguish correct from incorrect target; "
                    "they are not an admissible target-identification mechanism.",
        limitations=[
            "Does not disprove usefulness of supervised offset regression.",
            "Cycle statement applies to edges defined as exact node differences,not arbitrary learned edge fields.",
            "Additional target-conditioned supervised factors could break degeneracy but require new derivation.",
            "Static formula counterexamples,not native neural gradients or efficacy.",
        ])


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = audit()
    paths = [Path(__file__), root / "pipeline/reports/asphaltnet_original_20260916.pdf"]
    result["evidence"] = [dict(path=p.relative_to(root).as_posix(),
        sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
    out = root / "pipeline/reports/displacement_identifiability_20260916.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
