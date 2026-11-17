================================================================================
  T0 LMEC Formula Probe - cluster_project
  2026-09-11 19:07 +08:00
================================================================================

## 1. What Was Tested

CPU-only synthetic probes of the closed-form candidate score. No production
import, no dataset, no checkpoint, no CUDA. Implementation and raw results:

- `t0_lmec_formula_probe.py`
- `t0_lmec_results.json`

Tested formula:

    m_qn = sigmoid(mask_logits[q, n])
    v_q^+ = sum_n m_qn f_n / (sum_n m_qn + eps)
    v_q^- = sum_n (1 - m_qn) f_n / (sum_n (1 - m_qn) + eps)
    e_q = g(v_q^+, l) - g(v_q^-, l)
    s_q = u_q + lambda e_q

## 2. Gates That Pass

| Gate | Result | Evidence |
|---|---|---|
| G1 analytic vs finite-difference gradient | PASS | max abs error < 1e-6 over 12 mask logits |
| G2 whole-scene mask collapse | PASS | `m -> 1` gives `v+ = scene mean`, `v- = 0` |
| G4 point-axis permutation equivariance | PASS | permuting points leaves `e_q` unchanged to 1e-10 |

The quotient form is well defined and differentiable. Its exact mask gradient
is

    d e_q / d m_n = ( l . f_n - <l, v_q^+> ) / |support_q|
                  + ( l . f_n - <l, v_q^-> ) / |complement_q|

so no denominator gradient term is hidden: the normalized means cancel their
own derivative.

## 3. Defect B2 (Blocking): Complement Term Dominates

Holding one synthetic scene fixed and varying only the candidate mask area, the
evidence flips sign and is not monotone in area:

| Area | Positive term | Complement term | Evidence |
|---:|---:|---:|---:|
| 1 | 0.067 | -0.247 | 0.314 |
| 2 | -1.000 | -0.187 | -0.813 |
| 4 | 0.368 | -0.324 | 0.692 |
| 8 | 0.250 | -0.400 | 0.651 |
| 12 | 0.570 | -0.722 | 1.292 |
| 16 | 0.187 | -0.663 | 0.850 |
| 24 | -0.277 | -0.118 | -0.159 |
| 31 | -0.265 | 0.601 | -0.865 |

The complement mean is taken over `N - |support|` points. When the mask is tiny,
the complement mean still averages almost the whole scene, and the evidence is
dominated by a scene-level term rather than by the candidate's own support.
This reproduces the design-notes degeneracy "`e_q` can become a second unary
classifier". It is a real defect: the candidate score can move with mask area
independently of mask quality or language.

## 4. Observation O1 (Non-Blocking): Quotient Cancels Sigmoid Attenuation

The measured `d e_q / d mask_logit` grows with the logit scale and does not
decay at the expected `m(1-m)` rate. The area normalization cancels the sigmoid
factor. This is not by itself an instability, but it does mean the usual
confidence-calibration interpretation of `sigmoid(mask_logits)` does not carry
over: a highly saturated mask still produces a large logit-space gradient.
This needs an explicit derivation before any training claim about calibration.

## 5. Observation O2 (Open Risk): Single Language Direction

Within a scene every candidate shares the same language vector. For the
investigated affine and bilinear `g`, the language vector enters only as a
fixed direction applied to a candidate's margin. The synthetic probe cannot
decide whether that direction carries the intended semantic disambiguation;
that is an empirical question for a trained model, not something N1 or T0 can
settle. It is recorded as an open risk, not as a pass and not as a proven
failure.

## 6. Verdict

    admits_training = false
    quotient_form_is_well_defined = true

The current formula may not be implemented as a production mechanism. The
blocking defect is the area-dependent complement dominance (B2). A minimal
repair has to make the evidence term:

1. Compare support and complement on a common, bounded scale, for example by
   normalizing both by the scene-size factor or by using a symmetric
   support/complement form such as
   `e_q = g(v_q^+, l, |support_q|) - g(v_q^-, l, |complement_q|)` with an
   explicit area term, rather than two area-normalized means that are not
   comparable.
2. Keep the language direction identifiable after normalization, so the
   language-shuffle control can fail if the term is not semantic.
3. Preserve G1/G2/G4 and add a preregistered rejection: a matched area-only or
   language-shuffled control that reproduces the ranking gain rejects the
   mechanism.

Any repaired form is a new candidate and must repeat N1 and T0. No successor
variant is auto-enqueued.

================================================================================
  Status: T0 REJECT current formula | repair required | no training
================================================================================

## 7. Erratum (added 2026-09-11 20:07)

Gate `G2_whole_scene_support_collapses` was reported as PASS in section 2.
That label was incorrect. The probe showed that the support mean equals the
scene mean and the complement mean is zero, but the resulting evidence is
`<l, scene_mean>`, which is non-zero and carries no candidate-specific
information. The whole-scene case is therefore evidence FOR the second-unary
degeneracy, not a passed gate. See section 1 of `t1_lmec_repair_analysis.md`.
The rest of this document and the T0 rejection stand unchanged; the corrected
reading only strengthens the rejection.

================================================================================
  Status: T0 REJECT current formula | E2 erratum added | no training
================================================================================
