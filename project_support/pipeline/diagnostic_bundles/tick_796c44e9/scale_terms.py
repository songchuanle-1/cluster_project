"""Ordered scale terms and exact small-player attribution for diagnostics."""
import itertools
import math


def branch_terms(torch, points, banks, leaf, parent1, parent2, weights, masks_fn, heads=8):
    valid = len(leaf)
    if not valid:
        return [points * 0 for _ in banks]
    channels = points.shape[-1]
    dim = channels // heads
    query = points[:valid].reshape(valid, heads, dim).transpose(0, 1)
    masks = masks_fn(leaf, parent1, parent2, [len(bank) for bank in banks])
    terms = []
    for level, (bank, allowed) in enumerate(zip(banks, masks)):
        key = bank.reshape(-1, heads, dim).transpose(0, 1)
        scores = (query @ key.transpose(-1, -2)) / math.sqrt(dim)
        nonempty = allowed.any(dim=-1)
        scores = scores.masked_fill(~allowed.unsqueeze(0), -torch.inf)
        scores = torch.where(nonempty[None, :, None], scores, torch.zeros_like(scores))
        probabilities = scores.softmax(dim=-1) * allowed.unsqueeze(0)
        value = (probabilities @ key).transpose(0, 1).reshape(valid, channels)
        weighted = value * weights[:valid, level:level + 1]
        terms.append(torch.cat([weighted, points[valid:] * 0], dim=0))
    return terms


def shapley(values, players=3):
    assert set(values) == set(range(1 << players))
    assert all(math.isfinite(v) for v in values.values())
    result = []
    for player in range(players):
        total = 0.0
        for subset in range(1 << players):
            if subset & (1 << player):
                continue
            size = subset.bit_count()
            weight = math.factorial(size) * math.factorial(players-size-1) / math.factorial(players)
            total += weight * (values[subset | (1 << player)] - values[subset])
        result.append(total)
    residual = sum(result) - (values[(1 << players)-1] - values[0])
    assert abs(residual) <= 1e-12
    return result, residual


def cpu_controls():
    passed = []
    additive = {s: 7.0 + sum(v for i, v in enumerate((2.0, -3.0, 5.0)) if s & (1 << i)) for s in range(8)}
    got, residual = shapley(additive)
    assert all(abs(a-b) <= 1e-12 for a,b in zip(got,[2.0,-3.0,5.0]))
    passed.append({"name": "additive_and_negative_component", "values": got, "residual": residual})
    got, residual = shapley({s: 6.0 if s == 7 else 0.0 for s in range(8)})
    assert all(abs(v-2.0) <= 1e-12 for v in got)
    passed.append({"name": "pure_three_way_interaction", "values": got, "residual": residual})
    got, residual = shapley({s: float(s.bit_count() ** 2) for s in range(8)})
    assert all(abs(v-3.0) <= 1e-12 for v in got)
    passed.append({"name": "symmetric_game", "values": got, "residual": residual})
    for permutation in itertools.permutations(range(3)):
        mapped = {s: additive[sum(1 << permutation[i] for i in range(3) if s & (1 << i))] for s in range(8)}
        reordered, _ = shapley(mapped)
        assert all(abs(v-[2.0,-3.0,5.0][i]) <= 1e-12 for v,i in zip(reordered,permutation))
    passed.append({"name": "all_six_permutations", "passed": True})
    return {"passed": True, "controls": passed, "native_forwards": 0, "optimizer_steps": 0}
