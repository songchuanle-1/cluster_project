# M95 Contact Anchor Resolvability Preregistration

Stable ID `m95-contact-support-relation`; diagnosis only. Freeze the
256-expression contact screen SHA256
`cdaef8fc2fae29b47be303cd45356c7e6c11d6e65f2d1828972aaf62f6afe996`
and parsed graph audit SHA256
`d706fdba1ff98822d1740b19637d9d6ca13b3ce0099dabd05913ec62bc9d5a3d`.
Inspect exactly the 27 ambiguous color-independent contact expressions.

For each expression, take only graph edges with a fixed contact relation
(`top`, `under`, `below`, `against`, `attach`, `hanging`, `standing on`,
`sitting on`, `resting on`). Resolve `subject` against the scene's native
ScanRefer `object_name` descriptions using lowercased exact text after
whitespace normalization; exclude pronouns. Record zero, one or multiple
distinct `object_id` matches and whether it equals the target or a
same-class peer. This deliberately strict binding gives a lower bound on
deployable unambiguous anchors; it is not a semantic parser benchmark.
Report results separately for the 14 failures and 13 successes. Do not
choose anchors by target IoU or outcome. If few failures have a unique
physical anchor, this realization cannot support a matched target-versus-
peer contact intervention without additional native information. Neither
graph-edge presence nor a unique noun is an admission or novelty claim.
