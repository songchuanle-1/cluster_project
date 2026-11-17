# M95 Target-Blind RGB Support Diagnostic Preregistration

Stable ID `m95-visible-chromatic-support`. Freeze 256-expression M95
TRAIN capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`
and geometry binding SHA256
`bde38848d2036d3d2c5b71640a12190106214a0437b28931a9109eaaf238c085`.
This is a distinct input-channel test, not a repair of the failed centroid
boundary screen or a generic fusion/selector proposal.

For each deployed selected mask, aggregate the native unaugmented RGB points
by exactly bound superpoint index, then compute the selected-mask weighted
mean squared RGB distance of superpoint means from their weighted centroid.
Weights are point counts. This feature is target-blind; compute it before
stratifying selected IoU. Compare failure minus success in each scene when
a success exists and otherwise nearest-size cross-scene success, exactly
as in the frozen geometry match. Report the 56 deployed failures and the
16 no-acceptable-mask rows separately, with same-scene denominators.
Negative control: roll the RGB-superpoint association by one index within
the same scene, preserving RGB values, mask size and scene composition.
Rerun original feature to check determinism.

Expected direction for a chromatic-support deficit is higher dispersion
among limited masks after size matching, with a clearer original than
rolled-control difference. If absent or reversed, reject this RGB-
dispersion realization. Even a positive association would require a
target-specific, independently justified causal pathway, matched native
intervention, backward/resources and full goal gates. A color-word analysis
is independent and cannot be pooled with this screen as if it were the
same mechanism.
