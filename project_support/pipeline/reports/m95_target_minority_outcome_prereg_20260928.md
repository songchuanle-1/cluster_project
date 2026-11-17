# M95 physical target-minority exposure versus frozen TRAIN outcome

Stable candidate `m95-sample-context-support`, diagnosis only. Freeze the 128 native
TRAIN rows from `m95_target_seed_size_native_20260927.json`, transform seed 1999,
checkpoint/manifest hashes already bound in that artifact. For each unique
`(scene, ann_id)` recover the physical `*_refer.pth` data on authorized server-6
CPU. Verify its target instance tuple against the capture; do not select rows
by outcome. For every physical superpoint containing target points, calculate
the target point fraction. `minority` means `0 < fraction <= 0.5`, so native
`gt_spmask = (fraction > 0.5)` excludes that physical target fragment.

Primary diagnostic: count unique exposed expressions, scenes, target instances,
and target-bearing superpoints, without treating repeated descriptions as
independent. Failure is the frozen selected-mask IoU <= 0.5. Compare failure
rates exposed/unexposed by expression and by same-scene discordant pairs;
report all eligible denominators and missing data. Negative size control:
compare physical target-superpoint counts from the capture and total target
points; no numerical effect-size threshold or subset search. If exposure is
absent or not failure-linked, reject target-minority GT omission as the main
error mechanism for this cohort. An association alone is not causal because
small/thin objects and mixed geometry may confound it.

This is a prediction-blind source-bound diagnostic, not a deployable oracle,
matched native loss intervention, novelty proof, trained efficacy or admission.
Do not enqueue or tune thresholds from its result.
