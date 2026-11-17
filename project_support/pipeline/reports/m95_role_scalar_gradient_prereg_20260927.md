# Native focal scalar-gradient explanation test

Use unchanged checkpoint, fixed 16-batch/128-expression TRAIN cohort and
seed 1999 on server-6 GPU7. At the same 38 role triples/266 shared FPS
position comparisons, reconstruct each expression's exact native focal
sample loss and record the scalar `dL/d(ref_score)` and native logit for
target/context/zero arms. Preserve the sampler-input vector gradients.
Check frozen input fingerprints and complete physical bindings.

If target/zero negative vector-dot cases mostly coincide with opposite
scalar-gradient signs, while target/context alignments mostly share signs,
then label-dependent focal supervision is a sufficient directional
explanation; a new physical-role interaction is unsupported. Conversely,
discordant vector directions with identical scalar signs merit investigation
of language-dependent sampler Jacobians, not automatic admission. Report
all denominators by scene and physical position. No new objective, candidate
package or training. Do not change focal targets to manufacture a PASS.
