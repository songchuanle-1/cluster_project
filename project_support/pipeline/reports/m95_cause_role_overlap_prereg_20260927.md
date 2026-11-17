# Frozen cause/role cohort overlap audit

Stable diagnosis `m95-sample-context-support`, without a candidate model.
Input A is the 256-expression exact native M95 cause partition
`m95_exact_match_cause_partition_20260925-0715.json`, SHA256
`dc37eccc36a6903075ba26952f2be2ef664f728424101f2eb7960718b1de5bef`.
Input B is the 128-expression unchanged M95 TRAIN target-seed cohort
`m95_target_seed_size_native_20260927.json`, SHA256
`97d95b265b3e1a79e65f01748946f9eab9ff81d90efcfc05365894ddce58106c`.
Input C is the role-gradient comparison
`m95_role_gradient_native_20260927.json`, SHA256
`b01b4f0423ec08177cd8d1c4544f5615f1bd8b0abe80b31e8cb17cbe377b50a0`.

Before inspection: join A/B by `(scene,ann_id)` with unique bindings and
strict selected-IoU equality to catch cross-capture drift; do not treat a
failed join as a negative result. Among B's 128 expressions, report the
number with a deployed failure, the number whose all-native-positive
readback succeeds where deployed fails ("selection-recoverable"), and
the distribution of this stratum inside versus outside C's unique target
expression cohort. Within-scene comparisons are descriptive only. A
gradient conflict could motivate a new causal intervention only if the
role-gradient cohort actually covers an adequate set of
selection-recoverable failures. This screen cannot distinguish
mask-quality correction from score ordering and cannot establish a
novel supervision unit. No new model, queue or training is authorized by
an observational overlap.

Implementation failure before any overlap result: input A is a separately
selected 256-expression capture, not the same 128-expression seed cohort.
Only 32 `(scene,ann_id)` identities overlap, and 20 of those 32 disagree
on deployed selected IoU beyond the preregistered 1e-6 tolerance. The
binding/invariance guard must fail closed. Do not relax the join or
silently compute selection-recoverability on the remaining rows: this
would change both the declared estimand and provenance. The attempted
analyzer and test remain as an auditable failed attempt; output not created.
