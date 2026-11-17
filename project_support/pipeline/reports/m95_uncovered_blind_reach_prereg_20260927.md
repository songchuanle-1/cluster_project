# Prediction-blind geometric support-source falsification

On the same SHA-bound 256-expression TRAIN capture and exact physical
scene-to-superpoint binding, use preselected 16 mask-limited and 16
size-matched covered controls. Prior proximity tests used the
GT-defined target intersection of native matcher-positive query masks;
that source cannot be formed at inference. Replace it, before seeing
this result, with the Boolean union of *all 128 native predicted masks*.
For each physical target superpoint uncovered by every mask, compute
distance to the nearest superpoint in this target-blind source,
normalized by the scene median first-neighbor spacing. Compare to
the same expression's equally uncovered non-target superpoints of
the modal target semantic class and, separately, all uncovered
background. Target labels and categories select evaluation cohorts
only, not the support source. Validate finite native logits/mask
agreement, scene SHA256 and native superpoint indexing. No fitting
or threshold search.

Report the fixed four fragmented rows, the other 12 limited rows,
and 16 covered controls with absent-peer counts, medians and paired
direction. A useful prediction-blind local source needs a separation
not reducible to class-agnostic mask prevalence. If fragmented
rows lack same-class peers, mark that specificity test untestable;
do not substitute broad background as if it were same-class. This
is still a retrospective screen, not a causal mechanism, new loss,
inference rule, admission, or training result.
