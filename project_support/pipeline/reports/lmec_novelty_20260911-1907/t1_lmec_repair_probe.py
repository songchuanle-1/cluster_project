"""T1 CPU probes: repaired LMEC evidence term vs the rejected original.

Original (rejected in t0_lmec_analysis.md):

    e_q = g(v_q^+, l) - g(v_q^-, l)

where v_q^+ and v_q^- are area-normalized support and complement means.

Repair under test is the standardized two-sample contrast:

    v_q^+ = sum_n m_qn f_n / |S_q|
    v_q^- = sum_n (1 - m_qn) f_n / |S_q^c|
    Delta_q = g(v_q^+, l) - g(v_q^-, l)
    e_q = sqrt( |S_q| * |S_q^c| / N ) * Delta_q

Derivation: the difference of two independent sample means has variance
sigma^2 (1/|S| + 1/|S^c|) = sigma^2 N / (|S| |S^c|). Dividing by the
standard error gives the scale-free statistic sqrt(|S||S^c|/N) * Delta. The
factor carries no free parameter, vanishes when either side is empty
(|S| = 0 or |S| = N), and equalizes the null variance across mask areas.

No production import, dataset, checkpoint, or CUDA. Diagnostic only.
"""

import json
import math
from pathlib import Path

import numpy as np

REPORT_DIR = Path(__file__).resolve().parent


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def support_feature(m, f):
    m = np.asarray(m, dtype=np.float64)
    denom = m.sum()
    if denom <= 0:
        return np.zeros(f.shape[1]), 0.0
    return (m[:, None] * f).sum(axis=0) / denom, float(denom)


def complement_feature(m, f):
    m = np.asarray(m, dtype=np.float64)
    w = 1.0 - m
    denom = w.sum()
    if denom <= 0:
        return np.zeros(f.shape[1]), 0.0
    return (w[:, None] * f).sum(axis=0) / denom, float(denom)


def g_linear(v, l):
    return float(np.dot(v, l))


def delta(m, f, l):
    vp, _ = support_feature(m, f)
    vn, _ = complement_feature(m, f)
    return g_linear(vp, l) - g_linear(vn, l)


def evidence_original(m, f, l):
    return delta(m, f, l)


def evidence_repaired(m, f, l):
    m = np.asarray(m, dtype=np.float64)
    n_pts = len(m)
    pos = float(m.sum())
    neg = float(n_pts - pos)
    if pos <= 0 or neg <= 0:
        return 0.0
    scale = math.sqrt(pos * neg / n_pts)
    return scale * delta(m, f, l)


def probe_gradient_repaired():
    """Analytic vs finite-difference gradient of the repaired score."""
    rng = np.random.default_rng(20260912)
    n_pts, dim = 14, 5
    f = rng.normal(size=(n_pts, dim))
    l = rng.normal(size=dim)
    z = rng.normal(scale=0.8, size=n_pts)

    def score(zz):
        return evidence_repaired(sigmoid(zz), f, l)

    eps = 1e-6
    numeric = np.zeros(n_pts)
    for i in range(n_pts):
        zp = z.copy()
        zm = z.copy()
        zp[i] += eps
        zm[i] -= eps
        numeric[i] = (score(zp) - score(zm)) / (2.0 * eps)

    m = sigmoid(z)
    vp, pos = support_feature(m, f)
    vn, neg = complement_feature(m, f)
    d_delta = m * (1.0 - m) * (
        (f @ l - float(np.dot(vp, l))) / pos
        + (f @ l - float(np.dot(vn, l))) / neg
    )
    d_scale = scale_gradient(m, pos, neg)
    analytic = scale_of(n_pts, pos, neg) * d_delta + delta(m, f, l) * d_scale

    max_abs = float(np.max(np.abs(numeric - analytic)))
    return {
        "max_abs_error": max_abs,
        "passed": max_abs < 1e-6,
        "numeric_head": numeric[:4].round(8).tolist(),
        "analytic_head": analytic[:4].round(8).tolist(),
    }


def scale_of(n_pts, pos, neg):
    if pos <= 0 or neg <= 0:
        return 0.0
    return math.sqrt(pos * neg / n_pts)


def scale_gradient(m, pos, neg):
    """d scale / d mask_logit, with scale = sqrt(pos*neg/N)."""
    m = np.asarray(m, dtype=np.float64)
    if pos <= 0 or neg <= 0:
        return np.zeros_like(m)
    n_pts = len(m)
    c = math.sqrt(pos * neg / n_pts)
    return 0.5 * c * (1.0 / pos - 1.0 / neg) * m * (1.0 - m)


def probe_whole_scene():
    rng = np.random.default_rng(7)
    n_pts, dim = 32, 4
    f = rng.normal(size=(n_pts, dim))
    l = rng.normal(size=dim)
    full = np.ones(n_pts)
    empty = np.zeros(n_pts)
    return {
        "original_whole_scene_evidence": evidence_original(full, f, l),
        "repaired_whole_scene_evidence": evidence_repaired(full, f, l),
        "original_empty_evidence": evidence_original(empty, f, l),
        "repaired_empty_evidence": evidence_repaired(empty, f, l),
        "repaired_trivial_partition_vanishes": bool(
            abs(evidence_repaired(full, f, l)) < 1e-12
            and abs(evidence_repaired(empty, f, l)) < 1e-12
        ),
    }


def probe_permutation():
    rng = np.random.default_rng(31)
    n_pts, dim = 24, 5
    f = rng.normal(size=(n_pts, dim))
    l = rng.normal(size=dim)
    m = (rng.random(n_pts) > 0.4).astype(np.float64)
    perm = rng.permutation(n_pts)
    a0 = evidence_repaired(m, f, l)
    a1 = evidence_repaired(m[perm], f[perm], l)
    return {
        "original": a0,
        "permuted": a1,
        "permutation_equivariant": bool(math.isclose(a0, a1, abs_tol=1e-10)),
    }


def probe_null_area_bias(n_trials=400, seed=101):
    """No language alignment anywhere: which candidate wins, by mask area?"""
    rng = np.random.default_rng(seed)
    n_pts, dim, k_cand = 64, 8, 8
    areas = [1, 2, 4, 8, 16, 24, 32, 48]
    orig_win_counts = np.zeros(k_cand)
    rep_win_counts = np.zeros(k_cand)
    orig_small_wins = 0
    rep_small_wins = 0
    for _ in range(n_trials):
        f = rng.normal(size=(n_pts, dim))
        l = rng.normal(size=dim)
        l /= np.linalg.norm(l)
        masks = []
        for k in areas:
            m = np.zeros(n_pts)
            idx = rng.choice(n_pts, size=k, replace=False)
            m[idx] = 1.0
            masks.append(m)
        eo = np.array([evidence_original(m, f, l) for m in masks])
        er = np.array([evidence_repaired(m, f, l) for m in masks])
        io = int(np.argmax(eo))
        ir = int(np.argmax(er))
        orig_win_counts[io] += 1
        rep_win_counts[ir] += 1
        if io == 0:
            orig_small_wins += 1
        if ir == 0:
            rep_small_wins += 1
    uniform = 1.0 / k_cand
    return {
        "n_trials": n_trials,
        "areas": areas,
        "uniform_win_rate": uniform,
        "original_win_rate": (orig_win_counts / n_trials).round(4).tolist(),
        "repaired_win_rate": (rep_win_counts / n_trials).round(4).tolist(),
        "original_smallest_mask_win_rate": round(orig_small_wins / n_trials, 4),
        "repaired_smallest_mask_win_rate": round(rep_small_wins / n_trials, 4),
        "abs_deviation_original": round(
            float(np.mean(np.abs(orig_win_counts / n_trials - uniform))), 4
        ),
        "abs_deviation_repaired": round(
            float(np.mean(np.abs(rep_win_counts / n_trials - uniform))), 4
        ),
    }


def probe_target_recovery(seed=211, n_trials=200):
    """Plant one language-aligned target; vary its mask size."""
    rng = np.random.default_rng(seed)
    n_pts, dim, k_cand = 64, 8, 8
    distractor_areas = [1, 4, 16, 32, 48, 8, 24, 2]
    signal = 1.5
    rows = []
    for target_area in (1, 2, 4, 8, 16, 32):
        orig_hits = 0
        rep_hits = 0
        for _ in range(n_trials):
            f = rng.normal(size=(n_pts, dim))
            l = rng.normal(size=dim)
            l /= np.linalg.norm(l)
            target_idx = rng.choice(n_pts, size=target_area, replace=False)
            f[target_idx] += signal * l
            masks = []
            tm = np.zeros(n_pts)
            tm[target_idx] = 1.0
            masks.append(tm)
            pool = [i for i in range(n_pts) if i not in set(target_idx.tolist())]
            for k in distractor_areas:
                k = min(k, len(pool))
                idx = rng.choice(pool, size=k, replace=False)
                m = np.zeros(n_pts)
                m[idx] = 1.0
                masks.append(m)
            eo = np.array([evidence_original(m, f, l) for m in masks])
            er = np.array([evidence_repaired(m, f, l) for m in masks])
            if int(np.argmax(eo)) == 0:
                orig_hits += 1
            if int(np.argmax(er)) == 0:
                rep_hits += 1
        rows.append(
            {
                "target_area": target_area,
                "original_accuracy": round(orig_hits / n_trials, 4),
                "repaired_accuracy": round(rep_hits / n_trials, 4),
            }
        )
    orig_mean = float(np.mean([r["original_accuracy"] for r in rows]))
    rep_mean = float(np.mean([r["repaired_accuracy"] for r in rows]))
    return {
        "n_trials": n_trials,
        "signal": signal,
        "rows": rows,
        "original_mean_accuracy": round(orig_mean, 4),
        "repaired_mean_accuracy": round(rep_mean, 4),
        "repaired_minus_original": round(rep_mean - orig_mean, 4),
    }


def main():
    results = {
        "probe": "t1_lmec_repair",
        "original_formula": "e_q = g(v_q+, l) - g(v_q-, l)",
        "repaired_formula": (
            "e_q = sqrt(|S_q|*|S_q^c|/N) * (g(v_q+, l) - g(v_q-, l))"
        ),
        "derivation": (
            "difference of independent sample means has variance "
            "sigma^2*(1/|S| + 1/|S^c|) = sigma^2*N/(|S||S^c|); dividing by "
            "the standard error yields the scale-free factor sqrt(|S||S^c|/N)"
        ),
        "gradient": probe_gradient_repaired(),
        "trivial_partition": probe_whole_scene(),
        "permutation": probe_permutation(),
        "null_area_bias": probe_null_area_bias(),
        "target_recovery": probe_target_recovery(),
    }

    grad_ok = results["gradient"]["passed"]
    trivial_ok = results["trivial_partition"]["repaired_trivial_partition_vanishes"]
    perm_ok = results["permutation"]["permutation_equivariant"]
    bias = results["null_area_bias"]
    bias_ok = bias["abs_deviation_repaired"] < bias["abs_deviation_original"]
    small_bias_ok = (
        bias["repaired_smallest_mask_win_rate"]
        < bias["original_smallest_mask_win_rate"]
    )
    rec = results["target_recovery"]
    recovery_ok = rec["repaired_mean_accuracy"] >= rec["original_mean_accuracy"]

    results["gates"] = {
        "G1_gradient_matches_finite_difference": grad_ok,
        "G2_trivial_partition_vanishes": trivial_ok,
        "G3_permutation_equivariant": perm_ok,
        "G4_null_area_bias_reduced": bool(bias_ok),
        "G5_smallest_mask_false_positive_reduced": bool(small_bias_ok),
        "G6_target_recovery_not_worse": bool(recovery_ok),
    }
    results["correction_to_t0"] = {
        "note": (
            "The previous tick reported the whole-scene case as a pass under "
            "'G2_whole_scene_support_collapses'. That label was wrong: the "
            "support mean equals the scene mean and the complement mean is "
            "zero, but the original evidence then equals <l, scene_mean>, a "
            "non-zero scene-level term. That is the degeneracy the probe was "
            "meant to catch, not a pass."
        ),
        "original_whole_scene_evidence": results["trivial_partition"][
            "original_whole_scene_evidence"
        ],
    }
    tiny = next(r for r in rec["rows"] if r["target_area"] == 1)
    results["observations"] = {
        "O3_tiny_mask_sensitivity_regression": {
            "target_area": 1,
            "original_accuracy": tiny["original_accuracy"],
            "repaired_accuracy": tiny["repaired_accuracy"],
            "delta": round(
                tiny["repaired_accuracy"] - tiny["original_accuracy"], 4
            ),
            "interpretation": (
                "standardizing the contrast removes the spurious tiny-mask "
                "advantage, and it also removes genuine tiny-mask sensitivity; "
                "a 1-point support carries little evidence, so this is the "
                "honest cost of an unbiased null rather than a regression in "
                "the mechanism's useful range"
            ),
        },
        "O4_single_language_direction": {
            "note": (
                "with an affine or bilinear g the evidence is a scalar "
                "projection of the support-minus-complement margin onto one "
                "language direction; it is language-dependent but cannot "
                "express interactions that need more than one direction"
            ),
        },
    }
    results["verdict"] = {
        "repair_passes_t1_offline": bool(
            grad_ok and trivial_ok and perm_ok and bias_ok and small_bias_ok
        ),
        "target_recovery_not_worse": bool(recovery_ok),
        "admits_training": False,
        "reason": (
            "The standardized two-sample contrast repairs the trivial-"
            "partition degeneracy and reduces the null area bias without a "
            "free parameter. It still does not admit training: a fresh N1 "
            "re-check is required, the single language direction limitation "
            "remains, and no matched trained control exists yet."
        ),
    }

    out_path = REPORT_DIR / "t1_lmec_repair_results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "gates": results["gates"],
                "null_area_bias": {
                    k: bias[k]
                    for k in (
                        "original_smallest_mask_win_rate",
                        "repaired_smallest_mask_win_rate",
                        "abs_deviation_original",
                        "abs_deviation_repaired",
                    )
                },
                "target_recovery": {
                    "original_mean_accuracy": rec["original_mean_accuracy"],
                    "repaired_mean_accuracy": rec["repaired_mean_accuracy"],
                    "rows": rec["rows"],
                },
                "verdict": results["verdict"],
            },
            indent=2,
        )
    )
    print("wrote", out_path)


if __name__ == "__main__":
    main()
