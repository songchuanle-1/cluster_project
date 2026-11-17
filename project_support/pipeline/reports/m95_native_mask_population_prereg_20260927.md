# Native matched-mask loss, full limited population

Stable ID `m95-sample-context-support`. Extend the frozen four-row loss
subgraph probe to **all 16** expressions with no existing query mask IoU
above 0.5 in the same 256-row/220-scene TRAIN capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`.
The remaining 240 covered expressions provide 16 fixed size-matched
controls, selected without inspecting gradient signs. Require each
artifact hash, native matching, M95 loss source SHA256
`c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5`
and selected native IoU equality.

Replay final-layer `Criterion.loss_masks` with all matched queries,
and backpropagate unweighted BCE+Dice to final mask logits. Separate
matcher-positive and matcher-negative selected queries. For positives,
test the fraction of FN/FP superpoints whose gradient sign corrects
the native mask error; for negatives, do not assert direct referent
supervision. Report 16/240 denominators, distinct scenes, controls,
finite gradients and any missing support. This is a diagnosis of
loss-path availability, not trained benefit, new model backward or
the six-gate admission test.
