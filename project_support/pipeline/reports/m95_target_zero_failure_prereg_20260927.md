# Frozen target/zero conflict versus target-expression outcome

Stable diagnosis ID `m95-sample-context-support`. Source: unchanged M95
TRAIN seed1999 128-expression capture
`m95_target_seed_size_native_20260927.json` SHA256
`97d95b265b3e1a79e65f01748946f9eab9ff81d90efcfc05365894ddce58106c`
and physical-role gradient capture `m95_role_gradient_native_20260927.json`
SHA256 `b01b4f0423ec08177cd8d1c4544f5615f1bd8b0abe80b31e8cb17cbe377b50a0`.
Join `(scene,target_ann)` only, validate unique expression bindings, and
deduplicate target-expression physical positions
`(scene,instance,target_ann,fps_position)` to avoid double-counting
alternative zero annotations. Multiple context/zero expressions can yield
different pairwise gradients at one target position, so average the binary
dot signs over the one or two observed comparisons instead of requiring
equal dots. The source contains 133 distinct physical
positions overall; more than one target expression may share one of them.
The target expression's
selected mask IoU <= 0.5 defines failure. For each target expression, average
the fraction of negative target/zero dots over its physical positions; compute
target/context fraction as an existing-role control. Pair failure and success
target expressions within each scene; report exact eligible expression and
scene denominators. Never use per-position counts as independent samples.

Pre-analysis falsification: failure-linked cross-description target/zero
interference would have a consistently higher failure-minus-success
target/zero conflict fraction across paired scenes, but not a corresponding
target/context increase. Zero or sparse paired scenes are inconclusive.
This is observational gradient/outcome association, not evidence that such
conflict causes errors, and certainly not an independent training mechanism:
generic cross-expression contrast and PCGrad remain prior/closed. Do not
retarget focal labels or start training from this screen.

Implementation amendment before inspecting the result: the first test
failed because the 266 comparisons form 139 target-expression/physical
positions (127 doubletons, 12 singletons), while ignoring target
expression gives 133 physical positions. A second guard incorrectly
required the pairwise target/context dot to be identical across different
context expressions; it is not. The declared estimand remains the
target-expression position mean, averaged over available comparisons.
