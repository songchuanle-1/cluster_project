# Native matched-mask backward, four frozen failures

Stable ID `m95-sample-context-support`. Use the same frozen capture,
four mask-limited rows and four size-matched successful controls in
`m95_target_support_contract_20260927.json` SHA256
`0cc44842f05d713e2cc221de7f9a34ff4a59a3210d7b7d18c9ad9879de257cb2`.
Require exact M95 `loss.py` SHA256
`c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5`.

Replay `Criterion.loss_masks` with the frozen final logits and *all*
native-matched queries for each expression, repeating the captured target
union in native query order, and backpropagate the combined unweighted
BCE+Dice mask loss. This is a single-expression subgraph diagnostic,
not full-model native training. Check that every FN/FP of the selected
matcher-positive query has nonzero gradient in the corrective direction;
include the four fixed positive controls. The score MSE may be zero
because of its native IoU gate. Do not change matching or any coefficient.

If all four failures have corrective loss-logit gradients, an absent
final-mask-gradient explanation fails for this subset. The decoder
parameter Jacobian and competing losses can still cancel or dilute this
direction, and training efficacy remains unknown. Never interpret this
as a candidate's six-gate `native_backward` PASS.
