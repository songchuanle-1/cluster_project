# M95 context-error exposure across independent native transforms

Stable diagnosis `m95-sample-context-support`. Frozen 128-expression M95
TRAIN seed1999 and seed2000 sources:
`m95_seed_exact_1999_20260927.json` SHA256
`1dc93b87cf42526f5608fdd74641c949f58bf0fe3b7cc8a5cb90b1960110cbe7`
and `m95_seed_exact_2000_20260927.json` SHA256
`4765c45afa2706ddb949020ffab4226214eef80655c19abd5e6af3b19b5a5910`.
Require unique `(scene,ann_id)` and equal identity sets, frozen M95
checkpoint/manifest, different transform seeds, and changed recorded input
fingerprints for each expression. Selected wrong-context error is
`selected_seed_is_context` and selected mask IoU <= 0.5.

Before outcome comparison, compute the exposure counts, intersection/union,
same-identity transition table, and independent scene denominator. Include
selected-context but successful rows as a separate control. Treat expressions
in one scene as dependent. Prediction: a stable physical context-error
phenotype should persist for the same expression under the independent
transform more often than it disappears; if fewer persist, this particular
interpretation is not supported. This does not establish a novel mechanism,
causal benefit, or training admission. No oracle result is deployable.
