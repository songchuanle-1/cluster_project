# Native target-seed signed-gradient cancellation

Stable diagnosis ID `m95-sample-context-support`. Freeze the same 128 TRAIN
expressions and 32 scenes, transform seed 1999, checkpoint, native
`ref_scores` score derivatives and physical seed identity from
`m95_target_seed_size_native_20260927.json`. For each expression with at least
one target seed and nonzero total absolute derivative, define attraction
coherence `-sum(g_i) / sum(abs(g_i))`. Larger values indicate more net
attractive score derivative; a small value indicates within-target
cancellation. Do not interpret this as a feature-gradient cosine.

Before reading the result: within scenes having both failed and successful
expressions, test whether failure minus success coherence is negative. Report
scene-level signs and mean, zero/undefined denominators, and absolute
suppression-cancellation incidence. If the expected sign is not stable
across scenes, reject this particular cancellation explanation. This screen
is read-only; it cannot justify retargeting focal labels, a new training
candidate, or efficacy claims.
