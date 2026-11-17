# Prediction-blind support identifiability audit

Stable ID: `m95-sample-context-support`. Use the unchanged frozen 256-expression TRAIN union-intervention and feature-separability reports, verified by SHA256 before joining on manifest index, scene and annotation ID. No new checkpoint or inference-time target labels.

Question: do the 16 no-adequate-mask expressions lack target overlap in the prediction-blind all-query union, or does the union contain the target but the simple feature substitution still fail? Partition by union target overlap equal to zero versus positive, without selecting a threshold from outcomes. Report both groups' denominators, scenes, union fixed/harmed and selected-mask IoU changes. Use the 240 covered expressions as a specificity control and record target-size and same-category final-feature margin availability. This is an observational post-hoc audit: target labels define the diagnostic readout only, never a deployable support rule.

If union overlap is absent in most limited cases, no union-based mechanism can recover their missing support without another source. If overlap is present but substitution does not repair, the current union feature path remains disconfirmed; this alone does not identify a novel trainable alternative. No admission, queue mutation or efficacy inference follows.
