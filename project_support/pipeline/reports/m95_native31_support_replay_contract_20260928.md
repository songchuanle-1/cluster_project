# Frozen M95 support-replay contract check

Stable candidate `m95-sample-context-support`, diagnosis. This is a
prospective CPU-only correctness guard for
`m95_native31_same_forward_support_prereg_20260928.md`, not an observed native
intervention or new training method.

The native loss maps `sp_ref_masks` to FPS seeds, multiplies by 0.5, then
overwrites matched and nearest target seeds before focal loss. Equal changed
superpoint counts do not imply equal *final* focal-target perturbations.
Consequently the placebo must match treatment in the number and magnitudes
of changed final unprotected FPS seed targets within each original
expression and forward. Reject rows without a valid placebo; do not replace
rows or thresholds after inspecting outcomes. Protected target/nearest seeds
and every untouched seed must retain the exact final target. Baseline and
both arms must retain all non-sample criterion components. Compare repeated
baseline outputs on the same decoder prediction before interpreting a delta.

The fail-closed validator
`scripts/m95_native31_support_contract_20260928.py` checks these invariants
on aligned numeric vectors; six synthetic CPU tests cover matching,
overwrites, protected and off-target mutations, unequal counts/magnitudes,
and non-sample component drift. Together with the existing frozen adapter,
analysis, and lexical tests, 20 CPU tests pass. These tests do not verify
real eligible native seeds, gradient propagation, GPU resources, candidate
effect or any of the six admission gates. They must be applied to an
independently acquired, hash-verified same-forward native capture on
authorized server-6 GPU7 after foreign occupation clears.
