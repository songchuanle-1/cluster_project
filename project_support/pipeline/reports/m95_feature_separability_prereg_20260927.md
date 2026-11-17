# Frozen feature-separability diagnosis

Stable ID: `m95-sample-context-support`. Use the exact M95 TRAIN capture
SHA256 `68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`
and its hashed artifact set, the same 16 no-acceptable-mask expressions and
the 16 size-matched covered controls frozen by
`m95_native_mask_population_20260927.json` SHA256
`71159f4e74fcc19a72bdf13dd478d6ffe2a30b80823efeb41d6f59b3597800ea`.

Question: Does the final superpoint representation still geometrically
distinguish the physical target from same-semantic-category competing
instances, even when the mask readout is inadequate? Using physical labels
only for *post hoc* diagnosis, choose the modal semantic class of target
superpoints; require target and competing superpoints of that class in the
same scene. L2-normalize final features, take the mean target prototype and
report the difference between mean prototype cosine to target and mean
prototype cosine to same-class non-target instances. Report denominator,
ties, missing categories, scene overlap, and the full per-expression values
separately for limited and covered cohorts. Also report contrast from the
pre-encoder fused representation, on precisely the same superpoint supports.

This is an observational representation test, not a deployable mechanism or
a label-available intervention. Do not select a threshold after viewing the
data, infer trained benefit, or claim admission. A weak/strong contrast can
only guide a subsequent prediction-blind causal intervention and matched
new-model control. Preserve all sample and artifact hashes.
