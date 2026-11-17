# Frozen M95 missed-support modality retention

Use unchanged SHA-bound 256-expression TRAIN capture and the preselected
16 mask-limited plus 16 target-size-matched covered expressions. Restrict
to expressions with both target superpoints covered by at least one final
query mask and target superpoints missed by all 128 masks; exclude cases
without either part without replacing them. On the same physical superpoint
axis, compute the cosine of each missed target feature with the mean
covered-target feature prototype. Compare the within-expression mean
similarity to the mean similarity of still-uncovered non-target superpoints.
Do this independently in projected_3d, projected_2d, fused, and final
feature stages. Use the same frozen cohort, without reselecting scenes,
tokens, query index, positive set or parameters. Report paired expressions,
scenes, and per-row deltas; compare final to fused and the two projected
modalities. The negative control is same-expression uncovered background,
not a matched causal intervention.

If the image or geometry projected feature separates missed target
superpoints from equally uncovered background but fused/final does not,
that is a candidate information-loss diagnosis for a new mechanism.
If both are already separated or both fail, this specific modality
retention rationale is unsupported. This is GT-localized observational
diagnosis only. It cannot establish inference visibility, semantic
identity, new-model causality, efficacy or any admission gate.
