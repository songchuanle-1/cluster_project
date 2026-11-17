# Motivation Review - Provenance-Invariant Referent Supervision
2026-09-16 11:50 Asia/Shanghai. Mechanism derivation inside the newly opened axis.

## 1. Goal
pipeline/goal.json now carries 15 constraints (the 2026-09-16 scope decision B is the
newest) and 11 unchanged bans, target mIoU >= .51, Phase 1 NOT YET.
M95 ledger .5020 / exact .5024607181549072@16; baseline .4894491136074066@15.

## 2. What The Opened Axis Permits
B authorises structural changes to the referent *supervision*: a new loss, a new
positive-set definition, or a new supervision unit for the referent decision. It does
not relax anything else: Phase 1 still forbids tuning, FLOPs stay <= 10 G, the
independent-model/config, native-backward, resource, independence, receipt and
safe-sync chain still applies, and RefMask3D/DETR must not be presented as this
project's contribution.

## 3. The Measured Pathologies This Mechanism Must Address
| # | Measurement | Value |
|---|---|---|
| 1 | native referent positives per expression | 6.7 (824 total) |
| 2 | positives whose own mask reaches IoU > .5 with the target | 783 = 95.0% |
| 3 | queries whose own mask reaches IoU > .5 yet are labelled NO-OBJECT | **2455** |
| 4 | referent score by seed/mask cell | .047 / .130 / .848 / .876 |
| 5 | correct query's best rank among ALL acceptable queries | median 1, top-5 83.9% |
| 6 | deployed selection error when an acceptable query exists | 27.3% scene-balanced |
| 7 | oracle effect of restricting selection to positives | +17.9 pp, 22 fixed / 0 broken |
| 8 | objectness-only control | exactly null |
| 9 | nonlinear scene-held-out readout of the head's own input | 59-65% vs oracle 87.0% |

## 4. The Structural Reading
Facts 2 and 3 together are a **label contradiction at the hypothesis level**: among
queries whose predicted masks already cover the referred object, 783 carry the
referent label and 2455 carry the no-object label. The only thing distinguishing the
two groups is *provenance* - whether the query's sampled seed superpoint happened to
fall inside the referred instance. The head is therefore trained to answer a question
about the seed's location while deployment asks a question about the hypothesis.

Fact 4 confirms the head learned exactly the seed question; fact 9 shows it cannot
even recover that from its own input after the decoder's attention stack; fact 8 shows
that recognising "some object" is not the missing piece; fact 9 also rules out reading
the answer out of the existing features.

So the missing quantity is a supervision signal whose value depends on the
*hypothesis*, not on the hypothesis's *provenance*.

## 5. Prior Art Check, Done Before Designing
RefMask3D (2407.18244v1, ACM MM 2024, verified from the original PDF earlier in this
project) uses Hungarian matching with a cls+BCE+dice cost and then applies
Lmatch = l_cls L_cls + l_bce L_bce + l_dice L_dice to the matched object, plus a
contrastive term.

Decisive difference for this project's measured defect: **one-to-one assignment does
not remove the contradiction in fact 3.** It changes which single query receives the
referent label; every other query - including the 2455 whose masks cover the target -
is still supervised as no-object. RefMask3D therefore addresses *which query wins*,
not *whether the referent label depends on the hypothesis rather than on its
provenance*.

Related but distinct families checked: DETR-style set prediction with one-to-one
matching (same argument); IoU-aware / quality-aware classification in dense 2D
detectors (makes confidence depend on localisation quality, but for a dense anchor
per location, with no notion of provenance and no seed-derived positives);
set-based / cardinality losses (they change how the positive mass is normalised, not
what the label depends on); mask-aware contrastive alignment (re-weights existing
scores, and re-weighting was measured to fail here).

None of the verified works is aimed at a label whose value is fixed by the producing
seed rather than by the produced hypothesis. That is the specific, measured defect
this mechanism targets.

## 6. Proposed Mechanism
**Provenance-Invariant Referent Supervision (PIRS).**

The architecture, query set, matcher, mask losses, score loss and contrastive term are
all unchanged. Only the referent head's supervision changes:

1. **Target definition.** For query i, replace the binary provenance label
   1[seed_i inside referred instance] with a target that is a function of the query's
   own hypothesis quality, t_i = g(q_i) with q_i = IoU(mask_i, referred instance) and
   g monotone with g(0) = 0, g(1) = 1. Two queries with equal q_i therefore receive
   equal targets by construction - the contradiction in fact 3 cannot exist.
2. **No provenance term.** The referent loss (main and auxiliary layers) receives no
   seed-derived label anywhere. The seed continues to be used for mask/score
   assignment exactly as before, so this is not an assignment change.
3. **Warm start, not warm-up schedule.** Training starts from the existing M95
   checkpoint and the *same* epoch/max_iters budget; no schedule, warm-up window,
   weight sweep or curriculum is introduced. This is required by the constraint "整体
   统一修正前禁止单变体改 schedule" and by the Phase 1 no-tuning rule.

Formally, for query set Q with reference-instance mask M:
    q_i = |m_i ∩ M| / |m_i ∪ M|
    t_i = q_i                     (g identity, the only value used)
    L_ref = BCEWithLogits(s_i, t_i)
and the deployed score remains s_i, so the mechanism costs one elementwise IoU and one
soft BCE target per query: no new parameters and no new attention.

The single free design choice is g. The design fixes g as the identity and states no
sweep; if identity g fails the pre-registered criteria the mechanism is rejected
rather than re-parameterised.

## 7. Falsifiable Predictions And Pre-Registered Rejection
Admission of the *variant* (not of efficacy) requires the mechanical gates; the
scientific test is:

- **P1** After training, the referent score must stop being monotone in seed
  containment. Concretely the (seed+, mask-) mean score must fall below the
  (seed-, mask+) mean score, reversing the currently measured .848 vs .130.
- **P2** The correct query's best rank among all acceptable queries must stay at or
  improve from the current median 1 / top-5 83.9%, while the deployed-selection error
  must fall from 27.3% (scene-balanced).
- **P3** TRAIN selection success must exceed 69.1% by at least the goal's branch
  threshold, delta >= .002 on the pre-defined error stratum, reported with
  scene-level uncertainty.

Pre-registered rejection, any one of which ends the branch with no successor:
- the referent score remains monotone in seed containment (P1 fails), i.e. the head
  simply ignores the new target; or
- the selection error does not fall and TRAIN success does not exceed 69.1% + .002; or
- the head collapses to predicting the mask head's own quality without improving
  selection (measured as: referent ranking becomes a monotone function of mask IoU
  while the deployed selection error is unchanged); or
- peak memory rises by more than 15% with < +.003 mIoU, per the existing constraint.

## 8. Why This Is Not A Readout Or A Recombination
It changes the optimisation landscape, not the reading of existing scores: the same
logit s_i is decoded exactly as before, and no existing signal is re-projected,
re-weighted, re-ranked or gated. It also does not add a module, so it cannot be
described as "adding one operator at X"; the change is to the supervision target's
dependence structure (provenance -> hypothesis).

## 9. Next Batch
-> see pipeline/designs/exp_design_20260916-1150.md
Status: MECHANISM DERIVED / PENDING IMPLEMENTATION AND GATES.
