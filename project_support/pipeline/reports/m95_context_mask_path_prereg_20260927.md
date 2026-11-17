# Same-capture context seed to wrong-instance mask path

Stable diagnosis `m95-sample-context-support`. Frozen unchanged M95 TRAIN
seed-1999 native mask-reachability capture
`m95_seed_mask_reachability_1999_20260927.json`, SHA256
`e48cec2a0d4794cc1c14588afdd173bcafc310f2d71be0d0caa8778cde50f090`
is the only source; do not join to another capture. Verify 128 unique
`(scene,ann_id)` expressions, selected IoU range, and M95 checkpoint
and manifest binding. The selected query's sampled seed is bound to
physical instance; measure the binary selected mask IoU with that physical
instance. Report both greater-than-0.5 and mean same-instance IoU for
selected wrong-context failures, versus other failed expressions and
successful expressions. Aggregate descriptive group means by scene;
scene is the independent unit. The score/mask physical binding hypothesis
predicts greater same-instance coverage in the context-error arm than
other failures, despite equally failed target IoU. If direction reverses
and selected seeds outside masks are recorded as counterexamples.

This is a same-forward *readout* of one query, not a causal intervention.
Higher IoU cannot distinguish an ordinary seed-biased mask from a learned
referent mechanism, and no available deployable target identity signal is
established. Generic seed-mask consistency or selector changes remain
prior/closed; this test authorizes no model, resource gate or training.

Pre-result correction (08:45): first test stopped before writing a result
because two of the 128 selected seeds were outside their masks, both
successful non-context expressions. An all-row containment invariant was
not part of the causal estimand; count these counterexamples explicitly
by arm without dropping rows or changing the IoU comparison.
