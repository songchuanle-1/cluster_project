# M95 native-31 same-forward support intervention

Stable ID: `m95-sample-context-support`; stage: diagnosis. This document freezes
the *next* test before native outcomes are available. It is not a training
variant or admission receipt.

## Fixed inputs and sampling unit

- Use the exact 31-expression frozen manifest and checkpoint hashes from
  `m95_multiword_native_31_prereg_20260928.md`, native TRAIN scene groups and
  seed 1999. Require the adapter's source/data/checkpoint identity guards.
- Retain the native decoder output and all criterion arguments on each
  forward. For each expression, evaluate baseline, intervention and placebo
  against that *same* output, text tokens, geometry, FPS indices, query
  matching and target instances. Do not re-run the encoder or alter weights.
- Physical scene-target is the aggregation unit: seven units in two scenes,
  with repeated descriptions and reused controls explicitly dependent.
  Report each unit and the two scene aggregates; do not compute a row-level
  p-value or a two-scene confidence interval.

## Manipulations

- Baseline is the untouched native `sp_ref_masks`. Only expression rows with
  adjacent exact `shower curtain` tokens and a *non-target* physically labeled
  shower-curtain instance are eligible. Identify its superpoint occupancy
  from the unchanged physical instance/semantic labels. Preserve target
  superpoints; reject empty or ambiguous instance mappings.
- Treatment sets these non-target curtain superpoint-support entries to the
  support value that the native producer would assign for the phrase-aware
  class key, without changing any other source support. The single-word
  `curtain` class remains as originally produced. This tests a supervision
  path only, not a deployable linguistic parser.
- Placebo changes the same number of otherwise zero-supported non-target
  superpoints in the *same expression and same forward*, selected before
  looking at scores by stable physical-instance/seed ordering. Exclude
  shower-curtain and target instances; reject an expression if equal-count
  support cannot be constructed. Also replay the baseline once to verify
  deterministic criterion outputs.

## Readout and falsification

- Hook the criterion's *final* focal targets after matched-seed and nearest
  top-k overwrites. Count eligible FPS seeds surviving those overwrites.
  Verify treated and placebo changed the same number of eligible final seed
  targets, did not alter protected target/top-k seeds, and left all non-sample
  loss components invariant. Exclude insufficient-support rows rather than
  silently replacing a control.
- Predeclared directional prediction: treatment changes final weak seed
  targets and sample-loss gradients on the intended non-target support; the
  placebo should not yield the same target-specific pattern. Record finite
  scalar gradients to `ref_scores`; then on one native TRAIN forward test
  propagation to the existing sampling-module trainable tensors. No optimizer
  step; any query argmax or mIoU improvement requires a separately defined
  inference/training experiment.
- Reject this *realization* if no eligible final seeds remain, if treatment
  cannot be distinguished from its placebo, if native gradients are
  nonfinite/zero, or if unrelated loss components change. A limited two-scene
  cohort cannot establish general efficacy or novelty; all six admission
  gates and resource tests remain pending.

Only run on server-6 GPU7 after live occupancy is empty, an exclusive
diagnostic lease is acquired, and all original source/checkpoint/data hashes
are verified. A busy foreign process must be preserved.
