# Matched-positive-count control for fragmented M95 gradients

Stable `m95-sample-context-support` on frozen TRAIN capture. The previous
fragment-gradient join found four fragmented rows with fewer selected-query
mask-source gradients and more native-positive matches than the other 12
limited rows. To distinguish a trivial normalization-count explanation,
restrict to exactly two native-positive queries, the only count shared by
at least two rows in both arms. Compare the median selected query-gradient
norm and target feature-gradient norm, report all identities, scene counts,
native loss and missing strata. A persistent lower query norm contradicts
the *count-only* explanation but is not evidence of a new supervision unit.
No threshold tuning, inference selection, model change or training admission.
