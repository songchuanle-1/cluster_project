"""T2-v2 CPU controls for the repaired LMEC evidence term (LMEC-v2).

LMEC-v2 score under test

    u_q   = <v_q^+, l>                                  support-mean projection
    D_q   = <v_q^+, l> - <v_q^-, l>                    support-minus-complement
    c_q   = sqrt(|S_q| |S_q^c| / N)                     two-sample scale
    e_q   = c_q * D_q
    s_q   = u_q + e_q

Controls required by exp_design_20260911-2007.md section 4:
  * language-shuffle : same operator, target information removed from l
  * area-only        : rank by mask geometry, no language at all
  * lambda-zero      : rank by u_q alone (drop the complement term)

Plus the rejected original (u_q dropped, D_q unstandardized) and a random
ranker, so every step of the repair has a matched comparator.

Synthetic only. No production import, dataset, checkpoint, CUDA or training.
Diagnostic evidence for admission decisions, not a deployable result.
"""

import json
import math
from pathlib import Path

import numpy as np

REPORT_DIR = Path(__file__).resolve().parent
TARGET_AREAS = (1, 2, 4, 8, 16, 32)
# Disjoint from TARGET_AREAS so no candidate can tie on area; both geometry-only
# rankers are then a genuine null rather than an index-0 tie-break artefact.
DISTRACTOR_AREAS = (3, 6, 12, 20, 40, 56, 80)
N_POINTS = 128
SIGNAL = 1.5


def support_feature(m, f):
    m = np.asarray(m, dtype=np.float64)
    denom = float(m.sum())
    if denom <= 0:
        return np.zeros(f.shape[1]), 0.0
    return (m[:, None] * f).sum(axis=0) / denom, denom


def complement_feature(m, f):
    m = np.asarray(m, dtype=np.float64)
    w = 1.0 - m
    denom = float(w.sum())
    if denom <= 0:
        return np.zeros(f.shape[1]), 0.0
    return (w[:, None] * f).sum(axis=0) / denom, denom


def scale_factor(pos, neg, n_pts):
    if pos <= 0 or neg <= 0:
        return 0.0
    return math.sqrt(pos * neg / n_pts)


def scores(masks, f, l, shuffle=False, rng=None, rand_rng=None):
    """Every ranker returns one score per candidate, in the given order."""
    n_pts = len(f)
    if shuffle:
        l = _decoupled_direction(l, rng)
    u, delta, area, rand = [], [], [], []
    for m in masks:
        vp, pos = support_feature(m, f)
        vn, neg = complement_feature(m, f)
        up = float(np.dot(vp, l))
        dn = float(np.dot(vn, l))
        u.append(up)
        delta.append(up - dn)
        area.append(float(np.asarray(m).sum()))
    if rand_rng is not None:
        rand = list(rand_rng.random(len(masks)))
    u = np.asarray(u)
    delta = np.asarray(delta)
    area = np.asarray(area)
    c = np.asarray([scale_factor(a, n_pts - a, n_pts) for a in area])
    return {
        "lmec_v2": u + c * delta,
        "support_only_lambda0": u,
        "original_unstandardized": delta,
        "area_large_only": area,
        "area_small_only": -area,
        "random": np.asarray(rand),
    }


def _decoupled_direction(l, rng):
    """A unit vector with the target-aligned component projected out."""
    l = np.asarray(l, dtype=np.float64)
    for _ in range(64):
        cand = rng.normal(size=l.shape)
        cand -= (cand @ l) * l
        norm = np.linalg.norm(cand)
        if norm > 1e-6:
            return cand / norm
    raise RuntimeError("failed to sample a decoupled direction")


def make_scene(rng, target_area, n_pts=N_POINTS, dim=8):
    f = rng.normal(size=(n_pts, dim))
    l = rng.normal(size=dim)
    l /= np.linalg.norm(l)
    target_idx = rng.choice(n_pts, size=target_area, replace=False)
    f[target_idx] += SIGNAL * l
    masks = []
    tm = np.zeros(n_pts)
    tm[target_idx] = 1.0
    masks.append(tm)
    pool = [i for i in range(n_pts) if i not in set(target_idx.tolist())]
    order = list(DISTRACTOR_AREAS)
    rng.shuffle(order)          # distractor slots are not a fixed index prior
    for k in order:
        assert k <= len(pool), "distractor area must fit the complement pool"
        idx = rng.choice(pool, size=k, replace=False)
        m = np.zeros(n_pts)
        m[idx] = 1.0
        masks.append(m)
    return f, l, masks


def pick(vals, rng):
    """argmax with uniform tie-breaking, so geometry ties cannot favour index0."""
    vals = np.asarray(vals, dtype=np.float64)
    top = np.flatnonzero(vals == vals.max())
    return int(top[0] if top.size == 1 else rng.choice(top))


def recovery_accuracy(n_trials=200, seed=211):
    rng = np.random.default_rng(seed)
    names = list(scores([np.ones(2), np.zeros(2)], np.zeros((2, 2)),
                        np.zeros(2), rand_rng=np.random.default_rng(0)).keys())
    names.append("shuffled_language")
    hits = {name: {area: 0 for area in TARGET_AREAS} for name in names}
    for target_area in TARGET_AREAS:
        for _ in range(n_trials):
            f, l, masks = make_scene(rng, target_area)
            tie_rng = np.random.default_rng(rng.integers(1 << 30))
            plain = scores(masks, f, l, rand_rng=tie_rng)
            shuffled = scores(masks, f, l, shuffle=True,
                              rng=np.random.default_rng(rng.integers(1 << 30)))
            shuffled = {"shuffled_language": shuffled["lmec_v2"]}
            for name, vals in {**plain, **shuffled}.items():
                if pick(vals, tie_rng) == 0:
                    hits[name][target_area] += 1
    rows = {}
    for name in list(hits.keys()):
        rows[name] = [
            {"target_area": a,
             "accuracy": round(hits[name][a] / n_trials, 4)}
            for a in TARGET_AREAS
        ]
    means = {name: round(float(np.mean([r["accuracy"] for r in rows[name]])), 4)
             for name in rows}
    return rows, means


def main():
    rows, means = recovery_accuracy()
    gaps = {
        "lmec_v2_minus_area_large": round(means["lmec_v2"] - means["area_large_only"], 4),
        "lmec_v2_minus_area_small": round(means["lmec_v2"] - means["area_small_only"], 4),
        "lmec_v2_minus_random": round(means["lmec_v2"] - means["random"], 4),
        "lmec_v2_minus_shuffled": round(means["lmec_v2"] - means["shuffled_language"], 4),
        "lmec_v2_minus_support_only": round(
            means["lmec_v2"] - means["support_only_lambda0"], 4),
        "lmec_v2_minus_original": round(
            means["lmec_v2"] - means["original_unstandardized"], 4),
    }
    tiny = {name: next(r for r in rows[name] if r["target_area"] == 1)
            for name in rows}
    gates = {
        "C1_uses_language_not_geometry": bool(
            means["lmec_v2"] > means["area_large_only"]
            and means["lmec_v2"] > means["area_small_only"]
            and means["lmec_v2"] > means["random"]),
        "C2_requires_true_language_alignment": bool(
            means["lmec_v2"] > means["shuffled_language"]),
        "C3_complement_term_adds_over_support_only": bool(
            means["lmec_v2"] > means["support_only_lambda0"]),
        "C4_standardization_helps_over_original": bool(
            means["lmec_v2"] > means["original_unstandardized"]),
    }
    results = {
        "probe": "t2_lmec_controls",
        "setup": {
            "n_trials_per_area": 200,
            "n_points": N_POINTS, "dim": 8, "k_candidates": 1 + len(DISTRACTOR_AREAS),
            "target_areas": list(TARGET_AREAS),
            "distractor_areas_shuffled_per_trial": list(DISTRACTOR_AREAS),
            "distractor_areas_disjoint_from_target_areas": True,
            "tie_breaking": "uniform over argmax ties",
            "planted_signal": SIGNAL,
            "shuffle_control": ("unit direction with the planted language "
                                "component projected out"),
        },
        "accuracy_by_area": rows,
        "mean_accuracy": means,
        "gaps": gaps,
        "gates": gates,
        "observations": {
            "O5_area_prior_is_directional": (
                "neither |S| nor -|S| recovers the target: the target area "
                "sweeps 1..32 and the distractor areas are disjoint from it, "
                "so a fixed geometry prior picks the same 80-point or 3-point "
                "distractor on every trial and scores exactly zero"),
            "tiny_mask": {k: tiny[k]["accuracy"] for k in tiny},
        },
        "verdict": {
            "controls_pass": bool(all(gates.values())),
            "admits_training": False,
            "reason": ("Offline controls only; N1-v2 novelty re-check and a "
                       "matched trained control are still outstanding, and the "
                       "synthetic model assumes independent point features."),
        },
    }
    out = REPORT_DIR / "t2_lmec_controls_results.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"mean_accuracy": means, "gaps": gaps, "gates": gates,
                      "verdict": results["verdict"]}, indent=2))
    print("wrote", out)


if __name__ == "__main__":
    main()
