# Native Target Category Join Preregistration

Tick42f0e79c9e444f47808a5e16c9ea80d4; original deadline
2026-10-13T00:08:56.764352+08:00. TRAIN only; no validation/test selection.

Hypothesis: annotation object_name mapped by the native raw-name taxonomy
assigns a different target class from the physical target's native point
semantic labels, creating conflicting category supervision for one referent.
This is distinct from previously tested within-instance label homogeneity.

Freeze denominator all36665 TRAIN annotations /562scenes /7875physical
targets. Hash original dataset, annotation, taxonomy and each geometry input.
Use the original dataset mappings and object IDs; do not infer class from
caption keywords, parser root or external labels. Report unmapped names and
others separately, not as conflict or agreement.

Controls: same mapped class is identical; deliberately different non-others
native classes separate; missing/others are explicitly inconclusive.
Record disagreements, unique physical targets and expression counts.
Prediction-blind first disagreement per scene, sorted scene/object/ann,
may be examined for native transport only if mismatches actually exist.

Reject only this conflicting-category premise if all comparable native
annotation/physical-target classes agree. A positive mismatch is diagnosis,
not proof of harm, benefit, novelty or permission to train. Full native
backward/resources/independence/constraints remain pending, not PASS.
