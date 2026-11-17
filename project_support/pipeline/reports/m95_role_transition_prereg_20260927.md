# M95 same-scene physical role-transition feasibility

Stable diagnosis ID: `m95-sample-context-support`. Read the unchanged native
seed-1999 16-batch, 128-expression, 32-scene capture in
`m95_cross_expression_role_1999_20260927.json`. Validate the existing
preregistration's source hash and verify each scene has four expressions and
one shared collated-input fingerprint. A fingerprint includes text, so shared
scene membership, not equal full-input hashes, is the geometry control.

For each ordered expression pair (a,b) from the same scene with distinct
single target instances, ask whether a's target instance appears as an
unprotected non-target context seed of final native focal target 0.25 in b.
Record counts of scenes, pairs, distinct physical instance/role transitions,
eligible seed positions, and selected wrong-context failures on the b side.
Also count a's target instance as an unprotected zero-target physical seed in
b for a same-role negative-control denominator. Do not infer exact tensor
correspondence across expressions without captured per-expression FPS
superpoint IDs; instance identity is not seed index.

Feasibility requires at least one target-to-context role transition and
at least one selected wrong-context case; zero would reject the route's
coverage. This is observational incidence only. The proposed training
mechanism would compare evidence for the *same physical instance* under
target versus context expressions within the same scene. Before any native
backward or package, reject it as an independent core mechanism if its
whole loss reduces to existing object-text positive/negative contrast,
mask-aware matching, or referent ranking. A different pairing schedule
alone is insufficient. Do not enqueue from this screen.
