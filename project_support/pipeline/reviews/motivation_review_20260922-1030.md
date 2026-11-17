================================================================================
  Motivation Review - Referent Axis Evidence Reconciliation
  2026-09-22 10:30:00 Asia/Shanghai
================================================================================

## 1. Goal
pipeline/goal.json remains authoritative: ScanRefer mIoU must reach 0.51 while
Phase 1 forbids tuning. The champion is M95-CTF-HCG-CSORT at 0.5020
(0.5024607181549072 historical maximum); baseline model_base1 is 0.4894.
Server-6 GPU7 is the only dispatch-enabled target, with capacity 2. It is
currently occupied by a foreign das_env process and must not be disturbed.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Deployed referent-query selection is a real failure | confirmed | 8/16 selected-query successes on the bounded same-forward capture | Need a larger pre-registered cohort for a population estimate |
| Native-positive selection identifies a repair | bounded diagnostic | 15/16 successes; +43.75pp scene-balanced versus deployed | Oracle labels make this non-deployable |
| The repair is referent-specific rather than objectness-only | unresolved | Corrected any-seed control is 14/16; +37.5pp versus deployed | Both controls improve, so objectness remains a confound |
| Missing candidate coverage explains the failures | rejected | 0/16 expressions lacked an acceptable query in the new capture | Candidate coverage is not the current bottleneck |
| Same-class identity confusion explains all failures | unresolved | Only 2/8 failures are known same-class; 6 targets have semantic label -100 | Recover exact instance-semantic identity before choosing a mechanism |
| A new training mechanism is admissible now | rejected | No new causal information path separates referent identity from objectness | Mechanism design must wait for the semantic diagnosis |

## 3. Experiment Assessment
| Experiment | Result | Motivation View |
|---|---|---|
| Frozen M95 same-forward capture | 8/16 deployed success; 0 no-acceptable | Confirms selection error on a bounded cohort |
| Native-positive control | 15/16 success; +43.75pp | Confirms an oracle repair but is not deployable |
| Any-seed objectness control | 14/16 after fallback correction; +37.5pp | Shows the repair is not isolated to referent identity |
| Paired identity feature diagnosis | final target nearest-to-wrong 1/7; raw2d/fused agreement about 0.58 | Diagnoses bounded representation loss, not a mechanism |
| Prior selection/ranking/relation families | Rejected against measured controls or primary sources | No admissible successor from the old routes |

## 4. Gap Analysis
- Verified: the deployed selection is failing on the bounded capture.
- Verified: positive selection repairs most failures, but the objectness-only
  control also repairs most failures.
- Verified: all selected failures have an acceptable query in the same forward.
- Missing: exact semantic class for six target/wrong pairs because their sampled
  semantic labels are -100.
- Missing: a larger outcome-independent manifest with complete target, wrong and
  acceptable-query semantics, and a control rule that never falls back to the
  deployed argmax.
- Missing: a candidate mechanism with a causal unit not covered by RefMask3D,
  DETR, existing ranking, relation, or modality-fusion prior art.

## 5. Design Rationale
The corrected control invalidates the earlier "referent identity, not
objectness" claim on this capture. Designing a training variant now would bake
an unresolved confound into the queue. The next design must therefore be a
diagnostic sequence: recover semantic labels for the six unresolved pairs,
pre-register a larger same-forward cohort, and only then derive a mechanism.
The queue stays empty because candidate count is not a scientific objective.

## 6. Next Batch
See pipeline/designs/exp_design_20260922-1030.md. It defines two CPU diagnostics
and one larger GPU diagnostic; it admits no training variant and does not mutate
the queue.
================================================================================
  Status: MOTIVATION REVIEW COMPLETE (DIAGNOSTIC PLAN; NO TRAINING CANDIDATE)
  Reviewed by: Research Pipeline (autonomous)
================================================================================
