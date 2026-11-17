# M95 Explicit Color-Language Diagnostic Preregistration

Stable ID: `m95-explicit-color-scene-contrast`. This is a read-only TRAIN
diagnosis, not a model or a selector. Freeze the 256-expression manifest
SHA256 `4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`,
the exact native capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`,
and the selected-mask geometry screen SHA256
`45d333fc08a6f35b9b7f7741910977e3b8f3fbace2cde44cdd68e7869880c2f5`.
Only the original ScanRefer TRAIN description is used to define exposure;
neither selected IoU nor target identity enters the feature.

The exposure is presence of a standalone color token in the original
description, case-insensitive, from this fixed lexicon: red, blue, green,
yellow, orange, pink, purple, black, white, brown, gray, grey. Exclude
substrings and compounds. Match the exact scene/annotation/object triple
against the frozen manifest; reject ambiguous or missing joins. Outcome:
deployed selected-mask IoU <= 0.5. Report color incidence among 56 failures
and 200 successes, and separately among the 16 rows with no acceptable
existing mask. Partition by the manifest's ambiguous/class-unique stratum.

Controls: compare the failure rate against non-color expressions within
each stratum and report same-scene discordant-color pairs and denominators.
As a specificity control, run the same incidence calculation for a
predeclared spatial-word lexicon: left, right, front, behind, near, next.
This control is descriptive, not an interchangeable null intervention.
No threshold selection or test-set optimization is allowed. If color-bearing
failures are absent or not enriched relative to matched non-color controls,
do not advance a color-grounding mechanism on this cohort. If enriched,
next validate native scene RGB and target-versus-same-class distractor color
separability with a same-scene shuffled-RGB negative control before any
mechanism design. An association alone is not admission or proof of causality.
