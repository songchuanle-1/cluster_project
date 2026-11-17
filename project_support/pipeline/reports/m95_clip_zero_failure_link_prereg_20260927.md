# Frozen M95 failure-linked CLIP zero exposure

Stable candidate `m95-sample-context-support`, diagnosis only. The independent
physical cache audit found zero feature rows, but the first 64-scene annotation
cohort did not show target-specific enrichment. This screen joins the
already-frozen 256-expression M95 TRAIN native capture with its physical cache
rows without selecting examples or thresholds from outcomes.

For each expression bind its original superpoint IDs to the cache, require
cache row count to cover the maximum ID, and identify target superpoints by
strict majority physical instance ownership in the captured labels and the
frozen target instance IDs. Exposure is any target superpoint with an exactly
zero cache vector. Define failure as captured selected-query IoU <=0.5.
Report exposed and unexposed failure rates by unique scene as well as raw
expression counts; report same-scene exposure-discordant pairs, target
support and missing/unresolved rows. The negative control is non-target
zero-feature rate in the identical scene. Primary directional screen
requires target exposure to be enriched among failures and at least two
exposure-discordant scenes, not a fixed effect magnitude.

If the association fails or is driven by repeated descriptions, no
zero-feature repair variant follows. Even if positive, cache semantics,
matched same-forward native intervention, independent model path, backward
and resources remain unverified; this is not admission or efficacy.
