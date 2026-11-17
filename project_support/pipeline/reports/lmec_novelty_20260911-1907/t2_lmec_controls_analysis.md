================================================================================
  T2-v2 Offline Control Analysis - cluster_project
  Candidate: LMEC-v2 standardized two-sample contrast (UNADMITTED)
  2026-09-11 21:15 +08:00
================================================================================

## 1. What Was Run

`t2_lmec_controls_probe.py` (CPU only, synthetic, no production import,
dataset, checkpoint, CUDA or training). Results: `t2_lmec_controls_results.json`.

Every candidate ranker sees the same scene; only the scoring rule changes.
One target with area in {1,2,4,8,16,32} carries a planted language signal
`+1.5 * l`. Seven distractors have areas {3,6,12,20,40,56,80}, **disjoint from
every target area** and shuffled per trial, over 128 points. 200 trials per
target area. Argmax ties break uniformly, so no ranker can win through an
index-0 tie-break. An earlier draft of this probe used overlapping areas and
deterministic tie-breaking; that draft produced a meaningless 1.0 for a pure
random ranker and a spurious 1.0 for the geometry-only rankers. Those artefacts
are fixed here and the discarded numbers are not reported.

Rankers:

    lmec_v2               s = u + c * (u - <v^- , l>)      u = <v^+, l>
    support_only_lambda0  s = u                            (drop complement term)
    original_unstandardized s = u - <v^-, l>               (drop scale factor)
    shuffled_language     lmec_v2 with l projected off the planted direction
    area_large_only       s = |S|      area_small_only  s = -|S|
    random                uniform per candidate

## 2. Mean Target-Recovery Accuracy

| Ranker                  | Mean accuracy | Note |
|-------------------------|---------------|------|
| support_only (lambda=0) | 0.9592        | best ranker observed |
| original_unstandardized | 0.9592        | = support-only on this family |
| lmec_v2                 | 0.9292        | repair is *worse* than both |
| area_small_only         | 0.3333        | one trivial win, see O6 |
| shuffled_language       | 0.1792        | near chance 0.125 |
| random                  | 0.1117        | ~ 1/8 |
| area_large_only         | 0.0000        | fixed 80-point distractor always wins |

Per-area detail is in `t2_lmec_controls_results.json`.

## 3. Gates

| Gate | Statement | Result |
|------|-----------|--------|
| C1 | uses language, not geometry | PASS (.9292 vs .3333/.0000/.1117) |
| C2 | requires true language alignment | PASS (.9292 vs .1792 shuffled) |
| C3 | complement term adds over support-only | **FAIL** (.9292 vs .9592) |
| C4 | standardization helps over the original | **FAIL** (.9292 vs .9592) |

C1/C2 confirm the operator is a genuine language-alignment detector rather
than a geometric prior. C3/C4 are the gates that matter for the mechanism
claim, and both fail: adding the complement term *and* the two-sample scale
factor makes the ranker strictly worse than keeping the support mean `u_q`
alone.

## 4. Why C3/C4 Fail Here (mechanism reading, not a defence)

Under the independent-point noise model that the scale factor was derived
from, the complement mean carries no candidate-specific signal: it is a mean
of the same zero-mean noise as the support mean, with its own sampling
variance `sigma^2/|S^c|`. Subtracting it therefore removes a near-zero
quantity while adding variance, and rescaling by
`sqrt(|S||S^c|/N)` cannot restore information that was never present. So on
this family the repair is a *variance-increasing* operation on top of an
unchanged signal, and support-only wins.

This is the honest reading of the evidence produced. It is a falsification of
the complement term under an independent-point-feature model, not a proof
about real ScanRefer features, which are spatially correlated and where the
complement may contain structured context. That gap is exactly why the gate
is recorded as failed rather than as a universal disproof.

## 5. Observations

O6 small-area prior confound: `area_small_only` scores 0.3333, entirely from
target area 1, where the target is the smallest mask in the scene. The
smallest-area heuristic therefore coincides with the correct answer at that
one setting. This is the same tiny-mask degeneracy that motivated the
standardization and it confirms the effect is real in the generator.

O7 shuffled control is mildly above chance (0.1792 vs 0.125), concentrated in
the smallest target area (0.215 at area 1). This matches the T1 finding that
small supports inflate null win rates; the shuffle control is not perfectly
null even with the decoupled direction.

## 6. Verdict

- T2-v2 controls: **FAIL** (2 of 4 gates; both mechanism gates fail).
- N1-v2 novelty re-check: still outstanding (masked-attention and
  counterfactual/occlusion scoring literature remains unsurveyed).
- Admission: LMEC-v2 remains UNADMITTED. No config, model package, checkpoint,
  queue entry or trainer was created or changed by this probe.
- Per `exp_design_20260911-2007.md` section 7 rollback rule ("abandon LMEC
  entirely if N1-v2 or T2-v2 fails"), the correct next step is to close the
  LMEC mechanism rather than to search for a generator on which it wins.

================================================================================
