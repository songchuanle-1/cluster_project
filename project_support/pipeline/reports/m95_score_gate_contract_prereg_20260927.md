# Native mask-score gate, frozen M95 TRAIN population

Stable diagnostic ID `m95-sample-context-support`. Frozen full-capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`;
four-row mask-limited residual SHA256
`915e1d7e9385392a4f30da35a50b2698b54e005394caeb1d6d6a5ed2d3ca6bd5`.
The M95 native `Criterion.loss_masks` source gates score MSE at `get_iou > 0.5`,
while BCE and Dice still run for every matched query. Verify the source hash.

Count among all 256 frozen expressions how many native matcher-positive
queries receive mask-score supervision, and, separately, the four residual
selected matcher-positive queries. Use four fixed target-size-matched
success controls from the earlier support contract. Confirm the score gate
does not depend on physical seed identity and audit whether any positive
query exceeds 0.5 in each residual expression.

If all four selected residual queries are score-unsupervised, this is only
the existing score-quality target gate. It does not explain mask creation
or establish a new causal mechanism. PIRS/score-quality retargeting is a
closed direction; do not rename, tune gate/weight, admit or train a variant.
