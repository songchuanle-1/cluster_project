# Role-gradient capture coverage audit

Stable diagnosis ID: `m95-sample-context-support`. Freeze the M95 TRAIN
seed1999 target-seed capture `m95_target_seed_size_native_20260927.json`
(SHA256 `97d95b265b3e1a79e65f01748946f9eab9ff81d90efcfc05365894ddce58106c`)
and role-gradient capture `m95_role_gradient_native_20260927.json`
(SHA256 `b01b4f0423ec08177cd8d1c4544f5615f1bd8b0abe80b31e8cb17cbe377b50a0`).
No new capture or outcome-based selection.

Before inspecting output, define coverage as a unique `(scene,target_ann)`
having at least one role-gradient row. Compare failure prevalence
(`selected_mask_iou <= 0.5`) for covered versus uncovered expressions, and
report exact expression and scene denominators. Within scenes with both
covered and uncovered expressions, compare their failure fractions; never
count the 266 role comparisons as independent samples. Compare median
physical target-superpoint count across the arms as a target-size control.

The role-gradient audit can only support extrapolation to the full frozen
cohort if coverage is not strongly selected by task outcome or target size.
Large or sparse imbalances constrain generalization; their absence does not
prove exchangeability. This is a diagnostic sampling audit, not a training
mechanism, causal intervention, novelty claim, or admission gate PASS.
