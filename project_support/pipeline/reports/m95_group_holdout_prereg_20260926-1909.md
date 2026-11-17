# Independent TRAIN Group-Cue Diagnostic

Stable ID `m95-explicit-group-topology`. This follows the exploratory
seven-row audit, so those seven rows cannot serve as independent evidence.
Use native ScanRefer TRAIN descriptions SHA256
`018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d`
and frozen 256-row manifest SHA256
`4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`.
Exclude all 256 exact (scene, ann, object) keys.

Before inspecting model outcomes, select every remaining TRAIN expression
with standalone `bottom` or `lower` AND standalone `stack`, `stacked`,
`row`, `group`, `pair`, or `column`. Bind by exact scene, ann and object ID;
reject duplicates. For each physical scene, candidates are the target and
other physical instances with exactly the same ScanRefer object_name,
normalized only by lowercasing and whitespace. Require all IDs in the
original `_refer.pth` labels. Select the horizontally closest peer by
centroid, breaking distance ties by numeric ID. Record both the target
below-peer and reversed-z controls, physical XY distance, object-name
group, all excluded rows, and scene-file hashes. No distance threshold
or fitted axis. Absence of a peer is an unresolved case, not a success.

This rule is a probe, not a deployable mechanism: nearest peer is not
necessarily a referential group member. Its falsifier is missing or
ambiguous group binding, target-below-peer not exceeding the reversed
control on independently selected target-bound cases, or too few
independent scenes for a matched intervention. Even favorable physical
incidence is diagnosis only: preregister and execute true/shuffled
same-forward native model control, new-path backward, resource budget,
physical independence, and goal constraints before any admission.
