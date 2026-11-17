# M95 target-seed failures across native transforms

Stable diagnostic ID: `m95-sample-context-support`. This is an independent
error-partition screen, not a new model or a candidate admission.

Freeze the 128-expression native TRAIN captures at transform seeds 1999 and
2000, with SHA256 `1dc93b87cf42526f5608fdd74641c949f58bf0fe3b7cc8a5cb90b1960110cbe7`
and `4765c45afa2706ddb949020ffab4226214eef80655c19abd5e6af3b19b5a5910`.
Require identical unique `(scene,ann_id)` sets, checkpoint and manifest,
different input fingerprints on every expression, and identical target
physical-instance IDs. Define failure as selected mask IoU <= 0.5 and
target seed as `selected_seed_matches_target_instance`.

Count target-seeded failures per transform and their persistence, reporting
scene and expression denominators. Compare against persistent wrong-context
and other non-target-seeded failures under the *same* transform pair; report
transitions of selected seed identity and selected mask IoU without silently
excluding marginal 0.5 outcomes. Expected interpretation: if the same
target-seeded failures persist while seed labels remain target-positive,
then some errors are downstream of initial physical seed choice. If few
persist or selected seed identity changes, mark this branch uncertain.

This is observational and uses a small, selected TRAIN population. A target
seed does not establish a correctly bound query or a causal mask deficit.
Generic mask-quality correction, PIRS, selector changes and relabeled
ranking remain closed. Do not compare its fractions to validation efficacy
or admit training without a distinct mechanism and six full gates.
