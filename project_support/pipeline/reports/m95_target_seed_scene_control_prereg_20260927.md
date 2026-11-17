# Same-scene target-seeded mask failures

Stable diagnostic ID `m95-sample-context-support`. Freeze the two 128-row
native TRAIN exact-input captures and hashes from
`m95_target_seed_failure_prereg_20260927.md`. For each transform independently,
identify target-seeded selected mask failures (IoU <= .5), and compare only to
target-seeded successful expressions from the *same scene and transform*.
Require the same unique identity set and target physical-instance IDs across
transforms; report the numbers of eligible scenes and controls, failed and
control mask IoU, and the target physical-instance ID for every pair.

This diagnostic asks if physical target seed correctness alone is sufficient
for correct mask extent. If same-scene target-seeded controls succeed, the
failure is conditional on expression/query, not merely seed identity. If
controls involve different physical targets, do not call them matched-target
causal controls. No config, loss, seed selection, model, or gate is authorized
by this readout. A new mechanism still requires a deployable prediction-blind
signal and native same-forward intervention against original mask losses and
PIRS, then native backward, resources, independence and constraints.
