# Same-expression target-seeded query alternatives

Stable diagnosis `m95-sample-context-support`. The frozen full-TRAIN M95
capture SHA256 `68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`
contains 256 expressions with 128 native query masks each. Reuse only the
eight selected target-seeded failures (`ious[selected_query] <= .5`) from
the prior independently hashed full-population audit. For each expression,
bind every query seed with the audited
`physical_instance_labels[fps_superpoints[sampled_seed_indices[q]]]`.
Count *other* queries with a seed in the same physical target and native
mask IoU > .5, and report best other target-seeded query IoU, its native
indicator score/rank, selected score, and the scene denominator.

If acceptable same-target-seeded alternatives exist, that row is a
selection/score-ordering issue rather than evidence that the decoder
cannot form an adequate mask. If none exist, this frozen forward shows a
mask-limited row, but not a deployable causal mask-repair mechanism.
Do not turn an oracle alternative into an inference selector. Query masks
and GT serve diagnostic readout only; ordinary ranking and mask-quality
branches remain prior/closed. No new model, training or admission.
