================================================================================
  Motivation Review - Referent Exclusivity Supervision Rejection
  2026-09-17 22:13:00 Asia/Shanghai
================================================================================

## 1. Goal
pipeline/goal.json remains authoritative: target mIoU >= .51, champion M95 at
.5020, baseline at .4894, and Phase 1 is NOT YET. The goal excludes selector
changes as the main line, requires a novel lightweight structural mechanism,
and permits an empty slot when no candidate passes all scientific gates. The 16
constraints and 11 bans remain unchanged.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Referent identity is a causal failure axis | confirmed | Restricting deployed selection to native training positives raises scene-balanced success from 68.75% to 86.7%; the any-instance control is exactly null | no admissible non-prior-art mechanism |
| Correct hypotheses usually exist | confirmed | 118/123 fixed TRAIN expressions have a query above IoU .5; only 5 are mask-limited | deployable ranking calibration |
| PIRS repairs the failure | prior art | M197 remains running for pre-registered engineering evidence; SPFormer/RG-SAN already supervise query scores with mask quality | successor is disallowed |
| Referent-vs-distractor exclusivity is new | rejected | ConcreteNet already contrasts repeated same-class instances; prior decisions already reject hard-negative referent ranking | no distinct causal unit |

## 3. Experiment Assessment
| Experiment or Audit | mIoU / Result | Relation to motivation | Contribution |
|---|---|---|---|
| M197-PIRS | .4800 at 14/50, running | mask-quality referent score target | engineering evidence only |
| Positive-membership intervention | +17.9pp scene-balanced, 22 fixed / 0 broken | confirms identity selection failure | diagnostic evidence |
| Any-instance objectness control | exactly null | rules out objectness-only repair | negative control |
| Decision-aligned referent audit | rejected | listwise/top-1/ranking mechanisms are prior art | closes ranking family |
| Current exclusivity audit | rejected | PIRS successor plus hard-negative ranking | no implementation |

## 4. Gap Analysis
- Verified: the deployed query-selection rule discards available correct
  hypotheses and the loss of performance is tied to referent identity.
- Verified: objectness alone does not reproduce the gain, so a useful mechanism
  must depend on identity-discriminative evidence.
- Unverified: native same-class distractor overlap, relation binding, modality
  identity, and instance identity representation remain blocked behind GPU7.
- Contradiction: the most direct identity-margin loss is exactly the already
  closed hard-negative ranking family, not a new mechanism.

## 5. Design Rationale
The audited candidate multiplied the PIRS own-mask quality target by a penalty
for overlap with the hardest same-scene non-referred object. That would reward
hypotheses that are correct for the referred object and exclusive of repeated
distractors.

It is rejected before implementation. It is both a direct PIRS successor and a
hard-negative referent-ranking target, and the prior-art comparison is already
covered by ConcreteNet's contrastive repeated-instance supervision and the
instance-to-referent offset loss in arXiv 2411.03405v1. The operation is a
parameter-free recombination inside an existing score target, not a new causal
supervision unit or information path.

## 6. Next Batch
No candidate admitted; the one open design slot remains empty. Continue
M197-PIRS monitoring and the blocked native referent diagnostics. A future
candidate must leave the PIRS/mask-quality/ranking/same-target-consistency,
counterfactual-evidence, and selector families.

Evidence: pipeline/reports/referent_exclusivity_source_audit_20260917-2213.json
SHA256: b4107b831db04f6b6eba7e077c6ce8cafe8380f131df3b40117798781da9dd2e
================================================================================
