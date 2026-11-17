# M95 Target-Blind Geometry Screen Preregistration

2026-09-26 15:53 Asia/Shanghai. Stable ID
`m95-target-blind-mask-geometry-screen`; diagnostic only, no training.
Freeze the 256-expression native TRAIN capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`
and exact scene-to-support binding SHA256
`bde38848d2036d3d2c5b71640a12190106214a0437b28931a9109eaaf238c085`.

For every expression compute from the **deployed selected mask**, never the
oracle mask or GT: (a) mask size fraction of superpoints, (b) boundary edge
fraction on the undirected symmetric 6-nearest-centroid graph, and (c) induced
mask component count. The centroids are means of the unaugmented original
scene points mapped by the frozen `sample_inverse`; this axis binding has
already been verified for 256 rows/220 scenes. Record the native selected
IoU only after feature computation, to stratify failure versus success.

Matched control: compare a limited-mask case to a successful deployed case
in the same scene when possible, with minimum absolute difference in mask
size fraction; report the number of pairs and scenes. Secondary descriptive
control uses the nearest-size successful case from a different scene, with
no population or causal claim. Negative control: rotate the coordinate-to-
superpoint association within each scene by one index, keeping the same mask,
centroid set, adjacency degree and mask size but breaking its spatial
relation; recompute the boundary feature. Run the original feature on two
identical passes to verify repeatability.

Reject this route as a core mechanism if the observed separation can be
explained entirely by size, no same-scene support exists, shuffled geometry
is indistinguishable, or changes imply only posthoc mask expansion/
contraction, ranking, two-mask union, coverage repair, or BCCA. Even a
positive association is not causal or an admission: an independently
derived information path, matched native intervention and six gate receipts
would still be required. Never fit thresholds on the test split.
