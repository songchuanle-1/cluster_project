"""Offline exact conditioning identity audit; never imported by training."""
import itertools
import json
import math
from pathlib import Path


def log_partition(z, k):
    values = [sum(z[i] for i in subset)
              for subset in itertools.combinations(range(len(z)), k)]
    peak = max(values)
    return peak + math.log(sum(math.exp(v - peak) for v in values))


def terms(z, y, groups):
    n = len(z)
    global_z = log_partition(z, sum(y))
    component_z = sum(log_partition([z[i] for i in c], sum(y[i] for i in c))
                      for c in groups)
    score = sum(a * b for a, b in zip(z, y))
    # Independently enumerate the probability of the component-count event.
    weights = []
    event = []
    for selected in itertools.combinations(range(n), sum(y)):
        selected = set(selected)
        weight = math.exp(sum(z[i] for i in selected) - global_z)
        weights.append(weight)
        if all(sum(i in selected for i in c) == sum(y[i] for i in c)
               for c in groups):
            event.append(weight)
    log_event = math.log(sum(event) / sum(weights))
    return (global_z - score) / n, (component_z - score) / n, log_event


def main():
    maxima = dict(identity=0.0, gradient=0.0, shift=0.0, connected=0.0)
    cases = coordinates = 0
    for n in range(4, 9):
        for split in range(2, n - 1):
            groups = [list(range(split)), list(range(split, n))]
            y = [j % 2 for c in groups for j in range(len(c))]
            for pattern in range(5):
                z = [3 * math.sin((i + 1) * (pattern + 1)) for i in range(n)]
                lg, lc, lp = terms(z, y, groups)
                maxima["identity"] = max(maxima["identity"], abs(lc-lg-lp/n))
                assert lc <= lg + 1e-10
                shifted = [v + (2 if i < split else -3) for i, v in enumerate(z)]
                maxima["shift"] = max(maxima["shift"],
                                      abs(terms(shifted, y, groups)[1] - lc))
                cg, cc, _ = terms(z, y, [list(range(n))])
                maxima["connected"] = max(maxima["connected"], abs(cg-cc))
                for i in range(n):
                    plus, minus = z.copy(), z.copy()
                    plus[i] += 1e-5
                    minus[i] -= 1e-5
                    p, m = terms(plus, y, groups), terms(minus, y, groups)
                    err = abs(((p[1]-m[1])-(p[0]-m[0])-(p[2]-m[2])/n)/2e-5)
                    maxima["gradient"] = max(maxima["gradient"], err)
                    coordinates += 1
                cases += 1
    assert maxima["gradient"] < 1e-7
    assert all(v < 1e-10 for k, v in maxima.items() if k != "gradient")
    result = {"status": "PASS", "cases": cases, "gradient_coordinates": coordinates,
              "max_errors": maxima, "scope": "synthetic CPU algebra; no efficacy or novelty evidence",
              "identity": "Lc = Lg + log P(component counts | total count) / n"}
    path = Path(__file__).with_suffix(".json")
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
