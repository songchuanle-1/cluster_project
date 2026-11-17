# M95 full-TRAIN support diagnosis: failure specificity

Frozen source: `m95_full_train_outcome_link_20260928.json`, SHA256
`6472140a66dcab7dc275180fe3d56cb8a4ea67896477104d73c2a8f1d09df931`.
The 102 eligible TRAIN descriptions cover 28 scenes and 57 physical
scene-target units. Native selected-mask IoU < 0.5 for 15 descriptions in
four scenes and six physical units; 14 failures have score-matched replays,
and 13 of those have a lower treatment than placebo sample loss.

This loss direction is **not failure-specific**: the score-matched replay
also lowers loss for 69/73 replayable successes (82/87 overall).
Among four scenes containing both replayable failures and successes,
failed-minus-success mean loss contrasts are respectively +0.000364,
-0.002371, -0.000533 and -0.001271. Within the *same physical
scene-target*, only three units contain both outcomes: +0.000121,
-0.000129 and -0.000556. The sign is mixed. Descriptions and geometry
are dependent, and this is not a randomized effect estimate.

The source-level phrase repair cannot itself satisfy Phase 1 structural
novelty. The tested support intervention is physically supervised using
TRAIN instance labels and does not specify a deployable inference-time
mechanism. Its observed old-model gradient activity therefore remains a
diagnosis, not a candidate-native-backward or six-gate PASS. No new training
variant should be admitted or dispatched from this evidence alone.
