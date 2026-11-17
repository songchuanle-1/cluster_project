# Frozen M95 selected-query binding discrimination

Stable ID `m95-sample-context-support`. Use the frozen 256-expression capture
SHA256 `68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`
and its hash-checked feature artifacts. This is a read-only correction follow-up,
not a candidate implementation or training.

Bind query q's seed superpoint by
`fps_superpoints[sampled_seed_indices[q]]`; require it to equal the captured
`identity_query.sampled_superpoint_ids[q]`. For each expression's selected
query, report the number whose own predicted binary mask contains its seed,
separately for `native_positive` and native-negative selection. Include
the 256 total and missing-binding counts. Compare the positive and negative
fractions and the false-positive rate when using containment as a classifier
of correct referent selection.

If the negative fraction is also high, seed-in-mask containment supports a
query-to-mask path but cannot by itself serve as an identity-discriminating
training diagnosis. This does not override the separate native 17/17
context-exposed seed reachability or the noisy-OR directional rejection.
Do not use the earlier `sample_inverse[seed]` mapping. No training benefit,
causality or admission can be inferred from this observational screen.
