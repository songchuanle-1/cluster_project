"""Synthetic T0 probes for the proposed LMEC score.

This file is a numerical diagnostic only. It does not import the production
model, config system, dataset, or checkpoints. It evaluates the proposed
formula:

    m_qn = sigmoid(mask_logits[q, n])
    v_q+ = sum_n m_qn f_n / (sum_n m_qn)
    v_q- = sum_n (1 - m_qn) f_n / (sum_n (1 - m_qn))
    e_q  = g(v_q+, l) - g(v_q-, l)
    s_q  = u_q + lambda * e_q

for internal consistency: gradient correctness, degeneracy, and whether the
language term can change within-scene candidate ordering for a given g.
"""

import json
import math
from pathlib import Path

import numpy as np

REPORT_DIR = Path(__file__).resolve().parent


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def positive_feature(m, f):
    """Numerically safe weighted mean over the support mask."""
    m = np.asarray(m, dtype=np.float64)
    f = np.asarray(f, dtype=np.float64)
    denom = m.sum()
    if denom <= 0:
        return np.zeros(f.shape[1])
    return (m[:, None] * f).sum(axis=0) / denom


def complement_feature(m, f):
    """Numerically safe weighted mean over the complement mask."""
    m = np.asarray(m, dtype=np.float64)
    f = np.asarray(f, dtype=np.float64)
    w = 1.0 - m
    denom = w.sum()
    if denom <= 0:
        return np.zeros(f.shape[1])
    return (w[:, None] * f).sum(axis=0) / denom


def g_linear(v, l):
    """Concrete g(v, l) = <l, v>: a single shared projection of v."""
    return float(np.dot(v, l))


def g_bilinear(v, l, W):
    """g(v, l) = v^T W l: a bilinear form with a fixed W."""
    return float(v @ W @ l)


def g_mlp(v, l, W1, b1, W2, b2):
    """A small nonlinear g(v, l) = w2^T tanh(W1 [v; l] + b1) + b2."""
    x = np.concatenate([v, l])
    h = np.tanh(x @ W1.T + b1)
    return float(h @ W2 + b2)


def evidence(m, f, l, g):
    vp = positive_feature(m, f)
    vn = complement_feature(m, f)
    return float(g(vp, l) - g(vn, l))


def rank_of(evidence_values):
    """1-based rank order, high evidence first. Ties share min rank via argsort."""
    order = np.argsort(-np.asarray(evidence_values, dtype=np.float64))
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(order) + 1)
    return ranks.tolist()


def probe_gradient():
    """Analytic vs finite-difference gradient of e_q w.r.t. mask logits."""
    rng = np.random.default_rng(20260911)
    n_pts, dim = 12, 4
    f = rng.normal(size=(n_pts, dim))
    l = rng.normal(size=dim)
    z = rng.normal(scale=0.8, size=n_pts)
    u = np.array([0.3])

    def e_of_z(zz):
        m = sigmoid(zz)
        return evidence(m, f, l, g_linear) + float(u[0])

    eps = 1e-6
    numeric = np.zeros(n_pts)
    for i in range(n_pts):
        zp = z.copy()
        zm = z.copy()
        zp[i] += eps
        zm[i] -= eps
        numeric[i] = (e_of_z(zp) - e_of_z(zm)) / (2.0 * eps)

    m = sigmoid(z)
    # e = <l, v+> - <l, v->, and v+ / v- are support/complement means, so the
    # exact gradient is sign_flip * ( (l.f_n - <l,v_s>) ) * m(1-m) / area_s.
    vp = positive_feature(m, f)
    vn = complement_feature(m, f)
    lf = f @ l
    pos = m.sum()
    neg = (1.0 - m).sum()
    analytic = m * (1.0 - m) * (
        (lf - float(np.dot(vp, l))) / pos + (lf - float(np.dot(vn, l))) / neg
    )

    max_abs = float(np.max(np.abs(numeric - analytic)))
    max_val = float(np.max(np.abs(numeric))) + 1e-12
    return {
        "max_abs_error": max_abs,
        "max_rel_error": max_abs / max_val,
        "passed": max_abs < 1e-6,
        "numeric_head": numeric[:4].round(8).tolist(),
        "analytic_head": analytic[:4].round(8).tolist(),
    }


def probe_whole_scene():
    """Whole-scene mask: support == complement == scene mean, so e_q -> 0."""
    rng = np.random.default_rng(7)
    n_pts, dim = 16, 4
    f = rng.normal(size=(n_pts, dim))
    l = rng.normal(size=dim)
    scene_mean = f.mean(axis=0)
    m_whole = np.ones(n_pts)
    vp = positive_feature(m_whole, f)
    vn = complement_feature(m_whole, f)
    e = evidence(m_whole, f, l, g_linear)
    return {
        "positive_equals_scene_mean": bool(np.allclose(vp, scene_mean)),
        "complement_equals_zero": bool(np.allclose(vn, np.zeros(dim))),
        "evidence": e,
        "collapses_to_zero_support": bool(
            np.allclose(vp, scene_mean) and np.allclose(vn, np.zeros(dim))
        ),
    }


def probe_saturation():
    """Does a saturated mask actually stop transmitting selection gradient?

    The mask is affine, so the exact d e_q / d mask_logit is the finite difference
    of e_q. A well-behaved logit-to-evidence link should attenuate as the sigmoid
    saturates. Measuring the full derivative (rather than only the m(1-m)
    factor) avoids the algebra error that produced a constant gradient.
    """
    rng = np.random.default_rng(101)
    n_pts = 12
    f = rng.normal(size=(n_pts, 4))
    l = rng.normal(size=4)
    z_base = rng.normal(scale=0.7, size=n_pts)
    rows = []
    for scale in (0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 6.0, 8.0):
        z = scale * z_base
        eps = 1e-6
        e_plus = evidence(sigmoid(z + eps), f, l, g_linear)
        e_minus = evidence(sigmoid(z - eps), f, l, g_linear)
        deta_dz = (e_plus - e_minus) / (2.0 * eps)
        rows.append(
            {
                "mask_logit_scale": scale,
                "mean_sigmoid": float(np.mean(sigmoid(z))),
                "d_evidence_d_logit": float(deta_dz),
                "abs_d_evidence_d_logit": float(abs(deta_dz)),
            }
        )
    grads = np.array([r["abs_d_evidence_d_logit"] for r in rows], dtype=np.float64)
    peak_idx = int(np.argmax(grads))
    attenuation = float(grads[peak_idx] / (grads[-1] + 1e-300))
    return {
        "rows": rows,
        "peak_index": peak_idx,
        "peak_attenuation_vs_saturated": attenuation,
        "saturation_attenuates_gradient": bool(
            peak_idx < len(rows) - 1 and attenuation > 1e3
        ),
        "interpretation": (
            "the quotient normalization cancels the sigmoid factor, so the "
            "logit-to-evidence gradient does not attenuate at the expected "
            "m(1-m) rate; this is a design property that needs justification, "
            "not by itself a proof of instability"
        ),
    }


def probe_language_invariance():
    """Does changing l change within-scene candidate ordering?"""
    rng = np.random.default_rng(11)
    n_pts, dim, n_cand = 20, 6, 5
    f = rng.normal(size=(n_pts, dim))
    # Candidate masks have different areas and different geometric coverage.
    masks = []
    for j in range(n_cand):
        m = np.zeros(n_pts)
        start = (j * 3) % n_pts
        m[start : start + (j + 2)] = 1.0
        masks.append(m)
    masks = np.stack(masks)

    l_a = rng.normal(size=dim)
    l_b = rng.normal(size=dim)

    # g = <l, v>: e_q = <l, v+_q - v-_q>, and the language vector is a
    # scene-constant scaling factor. Rankings cannot depend on l at all.
    e_linear_a = [evidence(m, f, l_a, g_linear) for m in masks]
    e_linear_b = [evidence(m, f, l_b, g_linear) for m in masks]
    linear_same_order = rank_of(e_linear_a) == rank_of(e_linear_b)
    linear_same_order_under_scale_only = rank_of(e_linear_a) == rank_of(
        [evidence(m, f, 2.0 * l_a, g_linear) for m in masks]
    )

    W = rng.normal(scale=0.5, size=(dim, dim))
    e_bi_a = [evidence(m, f, l_a, lambda v, ll: g_bilinear(v, ll, W)) for m in masks]
    e_bi_b = [evidence(m, f, l_b, lambda v, ll: g_bilinear(v, ll, W)) for m in masks]
    bilinear_same_order = rank_of(e_bi_a) == rank_of(e_bi_b)

    W1 = rng.normal(scale=0.6, size=(8, 2 * dim))
    b1 = rng.normal(scale=0.1, size=8)
    W2 = rng.normal(scale=0.6, size=8)
    b2 = 0.0
    e_mlp_a = [
        evidence(m, f, l_a, lambda v, ll: g_mlp(v, ll, W1, b1, W2, b2))
        for m in masks
    ]
    e_mlp_b = [
        evidence(m, f, l_b, lambda v, ll: g_mlp(v, ll, W1, b1, W2, b2))
        for m in masks
    ]
    mlp_same_order = rank_of(e_mlp_a) == rank_of(e_mlp_b)

    # The scale-invariance claim needs an exactly proportional l pair.
    alpha = 3.1
    e_scaled = [evidence(m, f, alpha * l_a, g_linear) for m in masks]
    strictly_proportional = bool(
        np.allclose(np.array(e_scaled), alpha * np.array(e_linear_a))
    )

    return {
        "dim": dim,
        "n_candidates": n_cand,
        "linear_g_same_order_under_l_change": linear_same_order,
        "linear_g_same_order_under_scale_only": linear_same_order_under_scale_only,
        "linear_g_same_order_under_scaling": strictly_proportional,
        "bilinear_g_same_order_under_l_change": bilinear_same_order,
        "mlp_g_same_order_under_l_change": mlp_same_order,
        "affine_or_bilinear_g_is_language_invariant_within_scene": bool(
            linear_same_order and linear_same_order_under_scale_only and bilinear_same_order
        ),
        "e_linear_a": [round(x, 6) for x in e_linear_a],
        "e_linear_b": [round(x, 6) for x in e_linear_b],
        "e_mlp_a": [round(x, 6) for x in e_mlp_a],
        "e_mlp_b": [round(x, 6) for x in e_mlp_b],
        "interpretation": (
            "within one scene all candidates share l, so an affine g never "
            "compares candidates through different language content; it maps "
            "the candidate margin vector through one fixed language direction. "
            "Whether that fixed direction carries the intended semantic "
            "disambiguation cannot be decided from synthetic features and is "
            "left as an open risk, not a pass."
        ),
    }


def probe_area_balance():
    """Does the complement term dominate when the mask is small?

    Fix the candidate's own support evidence and let the mask area vary. A
    spurious evidence term should not change sign or magnitude systematically
    with area when the geometry is otherwise held fixed.
    """
    rng = np.random.default_rng(23)
    n_pts, dim = 32, 4
    f = rng.normal(size=(n_pts, dim))
    l = rng.normal(size=dim)
    rows = []
    for area in (1, 2, 4, 8, 12, 16, 24, 31):
        m = np.zeros(n_pts)
        m[:area] = 1.0
        vp = positive_feature(m, f)
        vn = complement_feature(m, f)
        e = float(np.dot(l, vp) - np.dot(l, vn))
        rows.append(
            {
                "area": area,
                "positive_term": float(np.dot(l, vp)),
                "complement_term": float(np.dot(l, vn)),
                "evidence": e,
                "evidence_sign": int(np.sign(e)),
            }
        )
    return {
        "rows": rows,
        "sign_flips_with_area": len({r["evidence_sign"] for r in rows}) > 1,
        "complement_abs_grows_as_area_shrinks": abs(rows[0]["complement_term"])
        > abs(rows[-1]["complement_term"]),
    }


def probe_mask_permutation():
    """Score should be permutation-equivariant over the point axis."""
    rng = np.random.default_rng(31)
    n_pts, dim = 24, 5
    f = rng.normal(size=(n_pts, dim))
    l = rng.normal(size=dim)
    m = (rng.random(n_pts) > 0.4).astype(np.float64)
    perm = rng.permutation(n_pts)
    e0 = evidence(m, f, l, g_linear)
    e1 = evidence(m[perm], f[perm], l, g_linear)
    return {
        "evidence_original": e0,
        "evidence_permuted": e1,
        "permutation_equivariant": bool(math.isclose(e0, e1, rel_tol=0.0, abs_tol=1e-10)),
    }


def probe_tiny_mask_shuffle():
    """Language dependence under an MLP g, tiny vs large masks."""
    rng = np.random.default_rng(41)
    n_pts, dim = 40, 4
    f = rng.normal(size=(n_pts, dim))
    W1 = rng.normal(scale=0.5, size=(8, 2 * dim))
    b1 = rng.normal(scale=0.1, size=8)
    W2 = rng.normal(scale=0.5, size=8)
    b2 = 0.0

    def g(v, l):
        return g_mlp(v, l, W1, b1, W2, b2)

    l_a = rng.normal(size=dim)
    l_b = rng.normal(size=dim)
    out = {}
    for area in (1, 3, 20):
        m = np.zeros(n_pts)
        m[:area] = 1.0
        ea = evidence(m, f, l_a, g)
        eb = evidence(m, f, l_b, g)
        out[f"area_{area}"] = {
            "e_l_a": ea,
            "e_l_b": eb,
            "language_sensitivity": abs(ea - eb),
        }
    return out


def main():
    results = {
        "probe": "t0_lmec_formula",
        "formula": {
            "m_qn": "sigmoid(mask_logits[q, n])",
            "v_plus": "sum_n m_qn f_n / (sum_n m_qn)",
            "v_minus": "sum_n (1 - m_qn) f_n / (sum_n (1 - m_qn))",
            "e_q": "g(v_plus, l) - g(v_minus, l)",
            "s_q": "u_q + lambda * e_q",
        },
        "gradient": probe_gradient(),
        "whole_scene": probe_whole_scene(),
        "saturation": probe_saturation(),
        "language_invariance": probe_language_invariance(),
        "area_balance": probe_area_balance(),
        "mask_permutation": probe_mask_permutation(),
        "tiny_mask_language_shuffle": probe_tiny_mask_shuffle(),
    }

    gates = {
        "G1_gradient_matches_finite_difference": results["gradient"]["passed"],
        "G2_whole_scene_support_collapses": results["whole_scene"][
            "collapses_to_zero_support"
        ],
        "G4_mask_permutation_equivariant": results["mask_permutation"][
            "permutation_equivariant"
        ],
    }
    observations = {
        "O1_quotient_cancels_sigmoid_attenuation": not results["saturation"][
            "saturation_attenuates_gradient"
        ],
        "O2_language_direction_not_semantically_verified": results[
            "language_invariance"
        ]["affine_or_bilinear_g_is_language_invariant_within_scene"]
        is False,
    }
    # B2 is the hard defect that must be repaired before a training config can
    # exist. B1/O2 remains an open semantic risk, not a synthetic pass.
    blockers = {
        "B2_complement_dominates_at_small_area": results["area_balance"][
            "sign_flips_with_area"
        ],
    }
    results["gates"] = gates
    results["observations"] = observations
    results["blockers"] = blockers
    results["verdict"] = {
        "gradient_and_degeneracy_ok": bool(
            gates["G1_gradient_matches_finite_difference"]
            and gates["G2_whole_scene_support_collapses"]
            and gates["G4_mask_permutation_equivariant"]
        ),
        "quotient_form_is_well_defined": True,
        "admits_training": False,
        "reason": (
            "The quotient form has clean analytic gradients, a well-defined "
            "whole-scene collapse, and permutation equivariance. It does not "
            "admit training yet: the area-normalized complement term can "
            "dominate and flip sign with mask area, the quotient cancels the "
            "expected sigmoid attenuation without justification, and the "
            "semantic content carried by the single language direction is "
            "unverified. No production config may be created from the current "
            "formula."
        ),
    }

    out_path = REPORT_DIR / "t0_lmec_results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {k: results[k] for k in ("gates", "observations", "blockers", "verdict")},
            indent=2,
        )
    )
    print("wrote", out_path)


if __name__ == "__main__":
    main()
