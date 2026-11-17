# Cross-positive final-feature gradient coherence in fragmented masks

Stable candidate `m95-sample-context-support`, frozen 256-expression TRAIN
M95 capture SHA256 `68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`.
The source replay in `m95_mask_feature_path_20260927.json` verifies the final
LayerNorm query-mask logits and reaches the final superpoint features.
For the four preselected fragmented limited rows, other 12 limited rows, and
16 frozen size-matched covered controls, independently backpropagate each
native matcher-positive query's BCE+Dice mask loss to target-superpoint final
features on the unchanged captured logits. Verify their summed gradient
reconstructs the previously captured aggregate native gradient and loss.

Primary readout in rows with >=2 positives: ratio of norm of mean individual
target-feature gradients to mean individual norms, grouped by arm and scene.
Post-result correction at 14:05: The first output used the twice-normalized
native aggregate as the numerator against unscaled individual gradients.
That is not the preregistered ratio and depresses the value by the number of
positives. Preserve the first output as invalid for coherence, recompute a
separate corrected output using unscaled individual gradients in both numerator
and denominator. The native replay still uses the double normalization for its
binding check.
Ratio near zero signals opposing updates to the shared feature path; ratio
near one indicates aligned updates. Compare the count-matched (two positives)
subset separately and preserve all one-positive rows as undefined, not zero.
Expected hypothesis direction is lower coherence for fragmented than
other limited. A reversed or similar result rejects the narrow
cross-positive-cancellation explanation. Even a positive result does not
establish a prediction-blind supervisory mechanism or authorize training.
No GT-guided inference selector, loss-weight adjustment, new-model gradient
or efficacy claim.
