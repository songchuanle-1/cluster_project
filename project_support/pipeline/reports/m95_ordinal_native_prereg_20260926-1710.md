# M95 Ordinal Native Order Diagnostic Preregistration

Stable ID `m95-explicit-ordinal-count`. Freeze manifest SHA256
`4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`
and parsed binding SHA256
`3db88c9dca9f37d9ca13cb555685c90ee05801bebdc1da81fb7a720c8a4a726d`.
Check the manifest hash before execution and fail closed on any mismatch.
Read only the three strict ordinal
rows 7, 10 and 44 and their original native TRAIN scenes. No IoU, score or
selected mask enters the coordinate computation.

Bind target and declared same-class peer IDs to original instance labels,
report count and centroid x/y/z of every candidate. For row 7, resolve
the literal `door` name in the original ScanRefer scene object list; report
all matching object IDs and whether the anchor is unique. Report the target
rank among same-class objects for x/y in both ascending and descending
orders, breaking ties by instance ID. For row 10, likewise report all
`table` IDs. Row 44 `first container` has no ordering origin or direction.
Do not select a favorable axis or sign from four alternatives. An
axis-reversal is a negative control; report its rank without substituting it
for an independently specified camera/viewpoint. Even if a rank happens to
match `second`, absence of a target-bound, unique physical frame and a
reproducible matched native intervention leaves diagnosis/controls failed.
The rule is fixed before reading scene coordinates; no model admission.
