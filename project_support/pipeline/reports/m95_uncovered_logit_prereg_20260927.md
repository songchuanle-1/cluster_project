# Frozen M95 uncovered-support logit test

Stable ID `m95-sample-context-support`. Use only the SHA256-frozen
256-expression TRAIN capture, the preselected 16 mask-limited expressions,
and 16 target-size-matched covered controls from the prior population report.
For each expression, select target superpoints missed by every one of the
128 thresholded query masks. In the same native forward, measure the maximum
pre-threshold mask logit across queries at each such target superpoint.
Compare with the maximum logit at non-target superpoints that are also missed
by every query, using the same expression as the pairing unit. Report the
number of expressions where this comparison is defined, superpoint counts,
medians, target-minus-background medians, and the fraction of uncovered
target superpoints with max logit in the fixed [-0.5, 0] band. Report the
same values for the covered controls. The fixed band is diagnostic, not a
searched operating threshold. Validate each stored binary mask equals
`logit > 0` exactly and all logits are finite.

If uncovered target logits are consistently close to threshold and
distinguishable from equally uncovered background while controls retain
specificity, a threshold/representation diagnosis remains possible. If
they are not separated, calibration of the existing mask scores is not an
independent mechanism. Either result is observational and GT-localized:
do not introduce a threshold, logit rescale, new variant, admission, or
training from this test. Scene counts and per-expression rows must be retained.
