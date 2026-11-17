# Full frozen TRAIN feature-separability census

Stable diagnostic ID `m95-sample-context-support`. Source remains M95
256-expression/220-scene frozen TRAIN capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`.
No checkpoint, sample, mask threshold, or model changes.

Extend the earlier 16/16 size-matched screen to all 256 expressions. For
each expression, use the post-hoc physical target and same-category other
instances on its exact superpoint support. Recompute the target-prototype
cosine margin for fused (pre-encoder) and final features using the *same*
algorithm as `m95_feature_separability_20260927.py`. Split by whether any
native query mask has IoU >0.5; report expression and distinct-scene
denominators, unavailable same-category competitor count, means and
per-expression values. Separately report, at scene level, the number of
scenes containing both limited and covered expressions and paired scene
mean final-minus-fused contrasts.

An across-population drop in final-feature margins is not a causal
mechanism if both error and covered cohorts share it. This is TRAIN-only,
uses target labels as an oracle readout and cannot justify an inference-time
target-prototype selector, training admission, or any validation claim.
