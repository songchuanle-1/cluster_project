# Valid-class prediction-blind support specificity

Stable diagnosis `m95-sample-context-support`. The frozen 256-expression
TRAIN census SHA256-bound in `m95_valid_semantic_peer_census_20260927-1632.json`
identifies every row with at least one target superpoint missed by all
128 masks and at least one physically non-target, unseen peer with the
same **valid** (`>=0`) semantic category. This set was selected from
semantics and mask visibility, *before reading this distance test*:
zero fragmented, one other mask-limited, two preselected covered controls,
and 30 remaining expressions in distinct scenes.

On the exact native scene-to-superpoint coordinate binding, compare each
missed target superpoint's median distance to the nearest point in the
outcome-blind union of 128 native predicted masks with the same-expression
unseen valid same-category physical peer median. Scale by the median
first-neighbor spacing of all scene superpoints. The negative control
rolls the Boolean union by half the scene superpoint width, preserving
support count but breaking its physical alignment; do not change the
scene coordinates, cohort, native masks or class labels. Report all
33 eligible expression/scenes, original and rolled target-closer counts
by preselected stratum and each paired difference. No threshold search,
resampling, or posthoc exclusions. Validate capture, artifact and scene
SHA256 and exact native axis.

If success rows show the same apparent spatial separation as failure
rows, the proximity observation is not a failure-specific deficit. If
the control separates equally well, the target-blind source adds no
physical evidence beyond class/scene structure. Neither outcome
constitutes a causal forward/loss mechanism, inference correction or
training admission; the two fragmented rows remain undefined.
