# Sampler Jacobian direction control

For the frozen 266 role-gradient comparisons in
`m95_role_gradient_scalar_native_20260927.json`, verify source SHA256
and all nonzero scalar gradient denominators. The sampler-input
gradient for expression e is `dL/dh = (dL/dz) (dz/dh)`. Therefore
Jacobian cosine equals feature-gradient cosine multiplied by the
sign of the two scalar factors. Compare target/context and target/zero
Jacobian cosine after physical-position deduplication and at scene
level. If target/zero Jacobians align despite negative raw feature
gradient dots, the raw conflict is accounted for by native focal
scalar signs, not evidence of a new physical-role coupling. If
Jacobian directions remain systematically opposed, investigate
language-conditioned Jacobians before any design. No claimed
causality, efficacy, or training admission.
