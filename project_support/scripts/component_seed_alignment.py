"""Pure identity accounting for native free-sampling diagnostic outputs."""
from collections import Counter


def support_bounds(total, observed_deltas):
    """Bound full matched-query mean differences when IoU differences lie in [-1,1]."""
    observed = len(observed_deltas)
    if total < observed or total < 0 or any(not -1 <= x <= 1 for x in observed_deltas):
        raise ValueError("Invalid bounded-metric observations")
    if total == 0:
        return dict(total=0, observed=0, missing=0, lower=None, upper=None)
    missing = total - observed
    return dict(total=total, observed=observed, missing=missing,
                lower=(sum(observed_deltas) - missing) / total,
                upper=(sum(observed_deltas) + missing) / total)


def alignment_plan(before, branches):
    """Use one common physical support for all paired branches; report losses."""
    counts = {"before": Counter(before)}
    counts.update({name: Counter(values) for name, values in branches.items()})
    common = set(counts["before"])
    for values in counts.values():
        common &= set(values)
    return {
        "common": sorted(common),
        "counts": {
            name: {
                "queries": sum(values.values()),
                "unique": len(values),
                "duplicates": sum(values.values()) - len(values),
                "excluded_unique": len(set(values) - common),
                "missing_from_before": len(set(counts["before"]) - set(values)),
                "new_vs_before": len(set(values) - set(counts["before"])),
            }
            for name, values in counts.items()
        },
        "indices": {
            name: {seed: [i for i, value in enumerate(sequence) if value == seed]
                   for seed in sorted(common)}
            for name, sequence in {"before": before, **branches}.items()
        },
    }


if __name__ == "__main__":
    # Identity tests only: no model or local native dataset execution.
    import itertools
    cases = 0
    for permutation in itertools.permutations([4, 7, 9]):
        plan = alignment_plan([4, 7, 9], {"global": list(permutation),
                                         "component": [9, 4, 7],
                                         "global_repeat": [7, 9, 4]})
        assert plan["common"] == [4, 7, 9]
        for seed in plan["common"]:
            assert permutation[plan["indices"]["global"][seed][0]] == seed
        cases += 1
    plan = alignment_plan([4, 4, 7], {"global": [4, 7, 9], "component": [4, 9]})
    assert plan["common"] == [4]
    assert plan["counts"]["before"]["duplicates"] == 1
    assert plan["counts"]["component"]["missing_from_before"] == 1
    assert plan["counts"]["component"]["new_vs_before"] == 1
    assert alignment_plan([1], {"global": [2]})["common"] == []
    assert alignment_plan([], {"global": []})["common"] == []
    assert support_bounds(2, [.2]) == dict(total=2, observed=1, missing=1, lower=-.4, upper=.6)
    assert support_bounds(1, [.2])["lower"] == .2
    assert support_bounds(0, [])["lower"] is None
    assert support_bounds(3, [])["upper"] == 1
    print(f"PASS {cases + 7} identity/bound tests; no native efficacy claim")
