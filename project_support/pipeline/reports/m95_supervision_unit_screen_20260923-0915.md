# Supervision Unit Screen

Scope: resume referent-supervision-axis in event mode, not a new candidate
review or experiment design. No training implementation or admission.

## Evidence And Proposed Unit
- Frozen follow-up: six exclusion scenes have 70 acceptable native-negative
  queries. Seven within-positive scenes have 30 acceptable positives and 60
  acceptable negatives. A binary native-positive label cannot order the failed
  and acceptable positives. These are observed labels, not parameter gradients.
- Consider one expression-level SET-MASS unit: input is the existing query
  indicator logits z_q and detached hard target-mask IoU u_q. Define A as the
  queries with u_q > 0.5, then
  L_set = logsumexp(z_all) - logsumexp(z_A).
- Target is the oracle acceptable set; empty A must be excluded and counted,
  not replaced by the max-IoU query. The present 40 rows are failure-selected.
- Gradient ownership: dL/dz_q = softmax(z_all)_q -
  1[q in A]*softmax(z_A)_q. No gradient passes through thresholded masks or A.
  Shared indicator/decoder parameters receive the resulting gradient; mask
  BCE/Dice is unchanged. No native backward has been executed.
- Matched control would keep code, initialization, schedule, denominator,
  normalization and resource measurement fixed, replacing A with the original
  native-positive set. Singleton A reduces exactly to ordinary multiclass CE.

## Disposition
REJECT this proposed unit before implementation: it is an acceptable-mask
positive-set relabeling plus listwise ranking over existing scores. It adds no
new input or information flow. This is within the already closed generic
mask-aware matching/ranking and rejected referent-supervision-unit families;
it does not supply the whole-mechanism difference required by USER-SCOPE-B.
This is a local algebraic equivalence screen, not a new literature novelty
claim. No external prior-art search was performed or needed to reject it.

The tempting alternative of supervising query identity against the newly
shared disjoint prototypes is not admitted either: support is absent in 24/40
scenes, prototypes require the true target, and an identity-alignment loss
alone does not distinguish it from the already closed identity-loss family.
The 16 available rows cannot establish a population or causal mechanism.

## Next Bounded Evidence
Before proposing another loss, use the existing 40 failure shards to count
exact duplicate masks within each expression and native-positive membership
within each duplicate class. Report unique-mask versus query denominators,
and whether identical masks have discordant labels. This is a diagnosis of the
supervision unit, NOT authorization for deduplication, a selector, weighting,
quality ranking, a new capture, or training. Share one implementation across
supervision and identity axes if this action is pursued.

## Sources
- pipeline/reports/m95_supervision_direction_20260923-0815.json
- pipeline/reports/m95_failure_followup_20260923-0540.json
- pipeline/reports/m95_joint_support_20260923-0915.json
- pipeline/research_work.json: rejected referent-supervision-unit disposition
- pipeline/goal.json: USER-SCOPE-B and unchanged Phase 1 constraints
