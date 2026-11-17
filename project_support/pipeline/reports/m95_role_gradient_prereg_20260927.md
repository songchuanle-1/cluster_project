# Native shared-seed role-gradient diagnostic

Stable ID `m95-sample-context-support`. Use unchanged M95 checkpoint
`fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`
on server-6 GPU7. Freeze the same 32-scene/128-expression TRAIN population,
transform seed 1999. The earlier read-only census found 44 target-to-context
and 306 target-to-zero ordered pairs within 32 scenes. Each scene is expanded
into four expressions with the identical native FPS superpoint positions.

Intercept the tensor entering `dec.sampling_module` after scene features
and FPS sampling. Reconstruct each expression's exact native focal sample
loss from the captured final target, weights and `ref_scores`, using the
same native focal criterion and pad mask. Compute its gradient with respect
to the sampler input, then for each target instance in expression a and
non-target role in expression b, gather the *same physical FPS positions*.
Only compare within a scene and validate same FPS index, same physical
instance at each gathered position, and same sampler input vector.

Primary readouts, at scene level: eligible role triples (a,b,c) where
one physical instance is a's target, b's unprotected context (0.25),
and c's unprotected zero target. At the *same FPS positions*, also
require a's final target to be positive. Report nonzero paired gradient
fraction, cosine and dot products for a/b versus a/c. Report zero-gradient
and missing triple denominators; do not construct an artificial cosine
when either side has zero norm. A conflict mechanism requires negative
dot product enrichment in a/b relative to a/c under the same
scene/physical-instance/seed-index comparison. If no triples exist, the
control is infeasible and this test cannot establish the mechanism.
For a follow-up negative control, shuffle expression-role assignments
within a scene preserving counts and the same captured tensors/logits;
a similar effect under shuffle rejects identity specificity.

This one capture diagnoses gradient flow only. No new training objective,
resource/independence gate, efficacy inference or admission. Generic
object-text contrast and PCGrad are existing mechanisms, so a conflict by
itself does not justify a new core-method claim.
