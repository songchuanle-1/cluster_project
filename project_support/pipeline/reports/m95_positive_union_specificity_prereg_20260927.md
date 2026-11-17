# Native-positive union specificity screen

Stable `m95-sample-context-support`, frozen 16 limited and 16 target-size-matched
covered controls. Join the SHA256-bound native-positive-union result with the
native-positive population and frozen fragmentation cohort. Reconstruct IoU
for the best-positive query, positive union, all-query union and equal-count
fixed-index negative union from TP/FP/target-size. Check that the best-positive
query matches the frozen native-positive audit for limited rows; bound covered
controls by the frozen native maximum IoU. Compare
the positive-union threshold crossing `<= 0.5 -> > 0.5` in limited cases and
reverse crossing in covered controls. No threshold search: 0.5 is the
existing error definition. Report all rows and scene denominators.

If positive union fixes a limited row but breaks covered controls, a generic
positive-set union is not a reliable deployable mechanism. Even no harm would
remain oracle-like because the native matcher-positive set is unavailable at
inference. This is a frozen TRAIN counterfactual audit, not new-model
backward, efficacy or admission.
