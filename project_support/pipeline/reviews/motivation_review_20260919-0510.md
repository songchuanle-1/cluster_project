================================================================================
  Motivation Review - Preterminal Referent Selection Gate
  2026-09-19 05:10:00 Asia/Shanghai
================================================================================

## 1. Goal
pipeline/goal.json remains authoritative: ScanRefer mIoU must reach 0.51 while
Phase 1 forbids tuning. The champion is M95 at 0.5024607181549072; baseline is
model_base1 at 0.4894491136074066. The current design slot is 1 because M197-PIRS
is the only active task against a capacity of 2.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Referent-query selection is the actionable error | confirmed | Positive-only oracle restriction gives +17.9pp scene-balanced; objectness-only control is null | No deployable core mechanism has yet been admitted as novel |
| Same-forward candidate coverage is limiting | rejected | 118/123 expressions have an acceptable query; only 5 are mask-limited; sampling loses 0/117 covered targets | Coverage cannot explain the main selection failures |
| PIRS tests the obvious provenance repair | running | M197 is at epoch 20/50, best 0.4859, native step 2799/4686 | Its branch-stop result is not terminal |
| A score-target successor is admissible now | rejected | SPFormer/RG-SAN establish mask-quality score supervision; listwise, exclusivity, and PIRS-successor variants are closed | No new causal supervision unit |
| Relation/2D identity fusion repairs selection | rejected | Same-forward 2D language alignment is near chance; RefMask3D already covers language-group mask identification | No language-aligned identity signal |

## 3. Experiment Assessment
| Route | Evidence | Motivation View |
|---|---|---|
| Positive-only oracle | +17.9pp, 22 fixed / 0 broken | Confirms selection is causal but is not deployable |
| Same-forward coverage | 118/123 covered; 5 mask-limited | Rules out the alternate coverage explanation |
| PIRS | Running, not terminal | Must preserve the pre-registered branch-stop test |
| Decision-aligned ranking | Rejected against Rank & Sort and SPFormer/RG-SAN | Renames the same score-ranking supervision |
| Referent exclusivity | Rejected as PIRS successor and hard-negative ranking | No independent causal unit |
| Same-target consistency | Rejected against TrackRef3D and ViewRefer | Same description-set supervision family |
| Language-guided query selection | Rejected against UniSpace-3D LGQS and goal scope | Selector main line is prohibited |
| Relation-conditioned identity transport | Rejected on diagnosis and prior art | 2D evidence is not aligned to referent language |

## 4. Gap Analysis
- Verified: the model often discards an acceptable query, so selection is the
  actionable failure.
- Verified: missing candidate coverage is uncommon on the fixed TRAIN cohort.
- Verified: PIRS is already testing the strongest direct supervision repair, but
  its source novelty is limited and its terminal result is pending.
- Unverified due to GPU cap: native candidate coverage, rank separation, and
  geometric confusability on the outcome-independent cohort.
- Missing: a genuinely new causal information path or supervision unit outside
  the already rejected selection, ranking, consistency, relation, and coverage
  families.

## 5. Design Rationale
Admitting another variant would require either a preterminal PIRS successor,
a renamed ranking/selectivity loss, or a coverage mechanism contradicted by
the fixed-TRAIN evidence. None is scientifically admissible. The correct action
is to keep the slot empty, preserve M197's branch-stop test, and retry the
already-defined native diagnostics after the recorded capacity condition.

## 6. Next Batch
No candidate admitted. The bounded CPU audit and hash-addressed evidence are in
pipeline/reports/design_admissibility_audit_20260919-0510.json.
================================================================================
  Status: MOTIVATION REVIEW COMPLETE (NO CANDIDATE ADMITTED)
  Reviewed by: Research Pipeline (autonomous)
================================================================================
