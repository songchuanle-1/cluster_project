# Residual cross-expression gradient audit

Use immutable native scalar-gradient capture SHA256
`cec227e442bcf490f9e6304c242376864b9a27f0590ea15390d71d7acc120fc6`.
Define residual conflict at one same-scene/physical-instance/FPS position as
target/zero input-gradient dot < 0 while their focal scalar derivatives
have the same sign. Deduplicate ordered role triples by
`(scene, target_ann, zero_ann, instance, fps_position)` and then by
`(scene, instance, fps_position)`. Count independent scenes, distinct
targets and physical positions. Bind target and zero expression deployed
selection IoU and selected-seed instance from the same captured forward.

This audit is descriptive, not a mechanism admission. If residuals occur
only in a narrow cluster of scenes/targets and do not isolate a consistent
wrong-reference endpoint, do not create a loss/gradient-surgery variant.
Even if error-linked, this cannot itself establish an independent
information path or a same-forward candidate intervention.
