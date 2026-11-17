# Target-instance native seed-gradient direction census

Stable ID `m95-sample-context-support`. Freeze original M95 checkpoint,
32-scene/128-expression seed-1999 TRAIN manifest and the native sampler
focal path. For every expression, bind sampler seed index through its
captured FPS superpoint to the physical target instance. Record valid
target-instance seeds, final focal labels, logits and native scalar
`dL_sample/d(ref_score)` for each; stratify by selected-mask IoU > 0.5
versus <= 0.5 and aggregate by scene. Verify native loss reconstruction,
old input fingerprints, label/instance binding and any missing denominator.
Do not infer a beneficial loss from a positive scalar gradient: soft
labels naturally have an optimum. A broad failure-enriched suppressive
gradient might motivate a distinct causal question, but altering the
label/weight or reinstating closed mask-aware matching is not an
independent method. No model/config, admission or queue.
