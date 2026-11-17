================================================================================
  T1 LMEC Repair - cluster_project
  2026-09-11 20:07 +08:00
================================================================================

## 1. Erratum On The T0 Record

The 19:13 T0 note reported a gate `G2_whole_scene_support_collapses = PASS`.
That label was wrong. What the probe actually showed is:

- `v_q^+` (support mean) equals the scene mean and `v_q^-` (complement mean) is
  zero when the mask covers the whole scene.
- The evidence is then `<l, scene_mean>`, which is non-zero.

So the whole-scene case does not collapse to zero evidence; it degenerates into
a scene-level term that carries no candidate-specific information. That is the
degeneracy the probe was written to catch. The corrected reading makes the
original formula worse, not better, and strengthens the T0 rejection.

## 2. Why The Original Form Failed

The original evidence is a difference of two area-normalized means:

    Delta_q = g(v_q^+, l) - g(v_q^-, l)
    e_q     = Delta_q

Two problems follow directly from the normalization:

1. **Trivial partitions.** As `|S_q| -> N`, the complement mean tends to zero
   and `Delta_q` tends to `<l, scene_mean>`. As `|S_q| -> 0`, the support mean
   tends to zero. Neither endpoint is a valid candidate contrast, but both
   still produce a score.
2. **Unequal estimator variance.** Treating point features as independent with
   common variance `sigma^2`,

       Var[Delta_q] = sigma^2 ( 1/|S_q| + 1/|S_q^c| )
                    = sigma^2 N / ( |S_q| |S_q^c| )

   A candidate with a 1-point mask has roughly 4x the standard deviation of a
   balanced mask. Because selection takes the maximum over candidates, the
   noisiest candidate wins most often. The mechanism is biased toward exactly
   the degenerate small masks we do not trust.

## 3. Derivation Of The Repaired Form

Divide the contrast by its standard error. With `sigma` absorbed into the
learned `g`, the scale-free statistic is

    e_q = sqrt( |S_q| * |S_q^c| / N ) * ( g(v_q^+, l) - g(v_q^-, l) )

with `N` the number of scene points and `|S_q^c| = N - |S_q|`.

Properties that follow from the formula, not from a fitted constant:

- **No free parameter.** The factor is fixed by the point count and the
  predicted mask area.
- **Trivial partitions vanish.** The factor is zero at `|S_q| = 0` and
  `|S_q| = N`, so empty and whole-scene masks contribute no evidence.
- **Balanced masks are most informative.** The factor peaks at `|S_q| = N/2`,
  which is the partition with the most independent information on both sides.
- **Comparable null variance.** Under the no-signal null, the statistic has
  approximately the same variance across mask areas, so the max-over-candidates
  step no longer favors small masks.

Gradient with respect to a mask logit `z_n`, with `m_n = sigmoid(z_n)`:

    d e_q / d z_n = c_q * dDelta_q/dz_n + Delta_q * d c_q/dz_n

    c_q             = sqrt( |S_q| |S_q^c| / N )
    d c_q / d z_n   = (c_q/2) ( 1/|S_q| - 1/|S_q^c| ) m_n (1 - m_n)
    dDelta_q/dz_n   = m_n (1 - m_n) [ (l.f_n - <l,v_q^+>)/|S_q|
                                    + (l.f_n - <l,v_q^->)/|S_q^c| ]

## 4. Probe Results

Implementation and raw output: `t1_lmec_repair_probe.py`,
`t1_lmec_repair_results.json`. CPU-only, no production import.

| Gate | Result | Value |
|---|---|---|
| G1 analytic vs finite-difference gradient | PASS | max abs error < 1e-6 |
| G2 trivial partition vanishes | PASS | `e = 0` at empty and whole-scene |
| G3 point-axis permutation equivariance | PASS | invariant to 1e-10 |
| G4 null area bias reduced | PASS | mean abs deviation from uniform 0.0706 -> 0.0125 |
| G5 smallest-mask false positive reduced | PASS | win rate 0.285 -> 0.125 (uniform 0.125) |
| G6 target recovery not worse | PASS | mean 0.8725 -> 0.8792 |

Null-bias detail: with eight candidates of areas `[1,2,4,8,16,24,32,48]` and no
language alignment anywhere, the smallest mask won 28.5% of trials under the
original form and 12.5% under the repair. The uniform rate is 12.5%. The
original form genuinely manufactured tiny-mask winners out of noise.

Target-recovery detail (one language-aligned target, eight random distractors):

| Target area | Original accuracy | Repaired accuracy |
|---:|---:|---:|
| 1 | 0.715 | 0.575 |
| 2 | 0.805 | 0.780 |
| 4 | 0.875 | 0.940 |
| 8 | 0.900 | 0.980 |
| 16 | 0.960 | 1.000 |
| 32 | 0.980 | 1.000 |

## 5. Honest Limitations

- O3: single-point targets got worse (0.715 -> 0.575). A 1-point support carries
  little evidence, so an unbiased null necessarily gives up that sensitivity.
  This is a real trade, not a free improvement, and it must be stated if the
  mechanism is ever written up.
- O4: with an affine or bilinear `g` the evidence is a single scalar projection
  of the support-minus-complement margin onto one language direction. It is
  language-dependent, but it cannot express interactions that need more than
  one direction.
- The variance model assumes independent point features with common variance.
  Real scene features are spatially correlated, so the factor is a first-order
  correction, not an exact standard error.
- These are synthetic probes. They can falsify a formula; they cannot show that
  it improves ScanRefer mIoU.

## 6. Verdict

    repair_passes_t1_offline = true
    admits_training        = false

The standardized two-sample contrast is a principled, parameter-free repair of
the two defects found at T0. It is still not an admitted mechanism:

1. The formula changed, so it is a new candidate and needs a fresh N1 novelty
   re-check against the same four sources plus the masked-attention and
   counterfactual-evidence literature noted as open risk.
2. No matched trained control exists. A language-shuffle and area-only control
   is required before any gain claim.
3. The single-direction limitation is unresolved.

No model package, config, queue entry, or trainer may be created from this
result. FIFO M189/M190/M191/M193 remains untouched.

================================================================================
  Status: T1 repair PASS offline | N1 re-check required | no training
================================================================================
