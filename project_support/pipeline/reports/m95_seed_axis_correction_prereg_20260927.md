# Frozen M95 query-seed axis correction

Use the exact frozen capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`
and its hashed feature artifacts. The old partition used
`sample_inverse[sampled_seed_indices[q]]`, but `sample_inverse` maps
points to superpoints while `sampled_seed_indices` indexes the FPS
superpoint array. Correct query q's superpoint to
`fps_superpoints[sampled_seed_indices[q]]`. Validate that this equals
the artifact's captured `sampled_superpoint_ids[q]`, and compare
old/corrected seed-in-own-mask counts across 256*128 queries and
native-negative selected queries. Preserve the old artifact and report
the correction as diagnostic/bug evidence, not a model admission.
