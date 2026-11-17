# Frozen query-gradient conflict between missed target and same-class peers

Stable `m95-sample-context-support`, diagnosis only. The best native-positive
mask query misses target superpoints in the 26-row physical-peer cohort, but
it covers zero same-class peers in both fragmented missed-target rows.
Test whether the *same query-state update* that raises logits on uncovered
target support necessarily raises peer logits, or whether ordinary mask
BCE supplies compatible target-positive / peer-negative directions.

Freeze the capture, peer-origin SHA256 and original M95 checkpoint. Rebuild
every selected positive query's final mask logits from checkpoint out_norm
and captured final superpoint features, rejecting max absolute error >1e-4.
For every eligible row, take the query's missed target superpoints and the
annotated physically present same-class peer superpoints. Compute analytic
unnormalized BCE-with-logits gradient to the normalized query: mean
`(sigmoid(logit)-1)*final_feature` over missed target, and mean
`sigmoid(logit)*final_feature` over peer. Report cosine and sign of the dot
product between the two gradient vectors. A positive cosine means gradient
descent can reduce both losses in the same first-order query direction; a
negative cosine means they conflict. Do not convert this into a learned
contrastive loss or a metric effect. Also report mean missed/peer logits,
peer mask coverage, and groups split by preselected frozen strata.

Controls: take the first equal-size physically non-target, valid-category
but different-class superpoints in index order as a negative-class
comparison; if unavailable, record undefined. No threshold search or
outcome-driven exclusion. This final-layer BCE probe excludes Dice, shared
decoder Jacobians and optimizer, so even a directional conflict is neither
a complete native gradient nor an admissible mechanism. Two fragmented
scenes remain insufficient for a generality claim.
