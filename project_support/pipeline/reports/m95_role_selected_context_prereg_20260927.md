# Frozen role cohort versus selected wrong-context failure

Stable ID `m95-sample-context-support`. Prediction-blind cohort binding uses
the unchanged 128-expression M95 TRAIN seed-1999 capture
`m95_target_seed_size_native_20260927.json` (SHA256
`97d95b265b3e1a79e65f01748946f9eab9ff81d90efcfc05365894ddce58106c`)
and its same-population role-gradient capture
`m95_role_gradient_native_20260927.json` (SHA256
`b01b4f0423ec08177cd8d1c4544f5615f1bd8b0abe80b31e8cb17cbe377b50a0`).
Require unique `(scene, ann_id)` identities and exact per-expression input
fingerprints and deployed selected IoU within 1e-6. The role cohort is the
set of gradient rows' `(scene,target_ann)`; the outcome is the seed capture's
`selected_seed_is_context` AND `selected_mask_iou <= 0.5`. Do not select
examples by outcome when constructing role coverage.

Report denominator and number of selected wrong-context failures covered by
the role cohort, with non-exposed failures and successes as descriptive
controls, and scene-level overlap. The hypothesis that the existing
role-gradient experiment even probes the known context-error phenotype is
incompatible with zero exposed failures in the covered cohort. This is a
representativeness screen, not a mechanism gate:
coverage alone cannot establish causal role conflict, a novel supervision
unit, native new-model backward, or trained efficacy. Do not infer an
effect from the cross-capture cause partition, whose binding failed.

Pre-result denominator correction (08:20): the first test stopped before
producing any result. The earlier four exposed failures came from a
separately selected 32-key subset, not this frozen 128-expression population.
The latter has 17 selected wrong-context failures by a source-only census.
The original "four" threshold is inapplicable; the coverage cohort and
outcome definition remain frozen. No result-dependent threshold is adopted.
