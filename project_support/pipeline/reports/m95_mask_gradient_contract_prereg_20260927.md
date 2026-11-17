# Native mask-gradient contract, frozen M95 TRAIN capture

Stable ID `m95-sample-context-support`. Use the same immutable 256-row capture,
four mask-limited matcher-positive queries and four fixed size-matched positive
success controls as `m95_target_support_contract_prereg_20260927.md`.
Verify capture, artifact, identity, selected-query and native IoU axes.

For selected matcher-positive queries, the native BCE-with-logits loss has
per-superpoint derivative `sigmoid(mask_logit)-target` before reduction.
Compute its absolute gradient over target missed support (FN), contaminant
selected support (FP), and all superpoints, plus the sign expected to correct
FN (negative) and FP (positive). Compare four failures and four controls
without tuning thresholds or changing a loss.

If all error superpoints have the appropriate nonzero gradient, reject an
absent-BCE-gradient explanation for these examples. It does not prove the
optimizer can repair them, or that Dice/score supervision is sufficient.
No novel variant, score-weight change, inference-time GT or admission follows
from this frozen retrospective calculation.
