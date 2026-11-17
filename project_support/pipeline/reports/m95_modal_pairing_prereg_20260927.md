# Modal pairing placebo

Stable `m95-sample-context-support`. The observed cross-modal cosine may
reflect modality-specific distributions or target-versus-peer sampling, not
aligned 2D/3D evidence. On the frozen 26 physical-peer cohort, reproduce
exactly the query-logit-matched target/peer pairs from
`m95_modal_hardpeer_v1`. For each scene/expression, retain every projected
3D vector and all score/GT evaluation axes. Replace the 2D vector at every
support index by the vector at the next index under a cyclic roll of the
entire scene superpoint axis (one-place shift, fixed before outcomes).
Recompute `1-cos(projected_2d, projected_3d)` for original and placebo, then
the target-minus-peer mean on the same pairs.

This is a negative control for cross-modal *pointwise* alignment, not a
physical same-class permutation or a new mechanism. To support this
diagnostic path, both fragmented rows must have original positive deltas
and each original-minus-roll contrast must be positive, while covered
controls must not show the same uniform pattern. Report cohort denominators
and differences; no post hoc seed/shift/threshold search. A pass remains
two selected TRAIN scenes and cannot establish new-model causality, efficacy,
or six-gate admission.
