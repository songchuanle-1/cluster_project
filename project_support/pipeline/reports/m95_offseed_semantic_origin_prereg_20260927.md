# Off-seed target-support semantic origin

Stable diagnosis `m95-sample-context-support`. Freeze the same 256-expression
M95 TRAIN capture, the four previously identified fragmented limited rows,
the other 12 limited rows and 16 frozen size-matched covered controls.
For each target superpoint missed by the union of native-positive masks but
covered by a native-negative query, inspect that query's sampled physical
seed superpoint. Compare its captured semantic class to the target's
majority physical semantic class. Record disjoint per-superpoint counts:
at least one same-class negative seed, only other-class negative seeds,
or only unresolved labels. Unknown labels remain unknown; never count
them as same-class. Also report target superpoints with no query support.

Hypothesis: off-seed target coverage in fragmented failures might be
concentrated in same-category distractor-seeded queries, motivating a
separate relation-binding diagnosis; if primarily other-category or
unresolved, category-peer transfer is not supported. This is a
same-forward TRAIN GT-localized observational test, not an inference
rule, matched intervention, novel loss, or admission.
