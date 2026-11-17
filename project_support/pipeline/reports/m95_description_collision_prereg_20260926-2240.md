# Same-scene description collision audit

Stable ID: `m95-description-label-collision`. This tests contradictory
TRAIN label provenance, not same-target alternate-description consistency.
Use exact native ScanRefer TRAIN annotations and the 256 frozen changed-producer
outcomes. Before examining outcomes, normalize case/whitespace and punctuation
to alphanumeric word tokens, without semantic paraphrase or synonym matching.
Within each scene, a collision exists only if an identical normalized full
description maps to at least two distinct `object_id` values. Multiple
annotations for the same object are not collisions. Report duplicate
identities, every frozen exposure and failure, 128/128 strata, and same-scene
discordant pairs. Count exact raw-string collisions separately as a stricter
control. Fail closed on duplicate frozen annotation identities.

Disconfirm if no collision exists in the frozen cohort, or collisions do not
link to failed rows. A collision by itself could reflect annotation ambiguity,
not a mechanism. No queue admission without matched native control, backward,
resources, independent implementation and constraints.
