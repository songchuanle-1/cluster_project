# Frozen exposed-target gradient specificity

Stable diagnosis `m95-sample-context-support`. The same-population audit
`m95_role_selected_context_20260927.json` established that 8/17
selected wrong-context failures are in the 20-target role-gradient cohort.
Before looking at gradient signs by outcome, freeze the following test using
`m95_role_gradient_native_20260927.json` SHA256
`b01b4f0423ec08177cd8d1c4544f5615f1bd8b0abe80b31e8cb17cbe377b50a0`
and `m95_target_seed_size_native_20260927.json` SHA256
`97d95b265b3e1a79e65f01748946f9eab9ff81d90efcfc05365894ddce58106c`.
Validate all 128 expression bindings, per-expression fingerprint and selected
IoU within 1e-6. Deduplicate role rows at
`(scene, target_ann, instance, fps_position)` and average repeated
context/zero comparison indicators at each physical position. Average by
target expression; scene is the independent unit, not 266 comparisons.

Among the eight covered exposed failures, compare the fraction of negative
target/context gradient dots against target/zero dots at matched positions.
Report exposed, covered unexposed failure and covered success denominators,
and within-scene exposed-success differences only where both exist.
For an identity-specific *context-conflict* story, exposed failures must
have context-negative fraction consistently greater than zero-negative
within their scenes, unlike the covered-success negative control. A zero
fraction or consistently reversed direction disconfirms that realization;
mixed or sparse scenes are inconclusive. This audit cannot prove a causal
training mechanism and does not license generic contrast or PCGrad.
