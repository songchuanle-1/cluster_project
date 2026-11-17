# M95 Scene-Region Language Preregistration

Stable ID: `m95-explicit-scene-region-evidence`. Use the frozen 256-row
TRAIN manifest SHA256
`4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`,
the frozen 256-row outcome artifact (prior color screen) SHA256
`44b6833d717401b691236e14f42a3849b6b66ebcf466ab3ee4cfb195b7bc007a`.
The native ScanRefer TRAIN description source is bound to SHA256
`018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d`.
No validation/test outcome is used.

Freeze case-insensitive standalone tokens `corner`, `middle`, `center`,
`centre`. Match scene, ann_id, and target object_id exactly, fail closed on
missing or duplicate source descriptions. Report exposure and failure
incidence for all 256, the ambiguous and class-unique strata, and
same-scene exposure-discordant pairs. Keep exact exposed descriptions for
manual target-modifier audit. The target ID and frozen failure flag are used
only for retrospective diagnosis, never as an inference feature.

Hypothesis: a target-bound room-region phrase could supply scene-relative
evidence absent from object-only matching. A token does not establish a
physical room frame, target binding, or causal effect. Advance only with
unambiguous target-bound phrases, a prediction-blind physical region frame,
and a matched native intervention against a shuffled-region control,
followed by native backward, resources, independence and goal checks.
Sparse, contrary, or reference-object-only exposure rejects this lexical
realization. Do not rename it as a selector, generic relation, or ranking
variant.
