================================================================================
  Motivation Review — cluster_project
  2026-09-03 20:13:00
================================================================================

## 1. Goal
  - goal.json metric: mIoU >= 0.5100 on ScanRefer.
  - description: multi-scale cluster context is aggregated into a cluster bank and
    written back to instance features; explicit routing is disproven and context is
    the supported mechanism.
  - baseline: model_base1=0.4894.
  - champion: M95-CTF-HCG-CSORT=0.5020.
  - gap: +0.0080 to target.
  - constraints: FLOPs <=10.0G; unchanged schedule; Phase 1 structural mechanisms
    only; seed 1999; no N^2 point attention; all banned directions remain active.

## 2. Story Status
  | Hypothesis | Status | Evidence | Gap |
  |------------|--------|----------|-----|
  | Multi-scale cluster context improves grounding | confirmed | A1=0.5012 vs baseline=0.4894 | Need robust improvement beyond 0.5020 |
  | Explicit routing improves delivery | disproven | A3=0.4468 | Closed |
  | Static aligned foreground retrieval is object-semantic | disproven | M161 aligned=0.4920; M162 shuffled=0.4980 | Shuffled distribution is stronger than alignment |
  | Generic scene/distribution context masks an object-specific residual | untested | M162-M161=+0.0060 for shuffled over aligned | Primary new causal gap |
  | Alternative prediction-conditioned mechanisms help | testing | M163/M166 running; M164/M165/M167-M169 waiting | Await results |

## 3. Experiment Assessment
  | Experiment | mIoU | Relation to motivation | Story contribution |
  |------------|------|------------------------|--------------------|
  | M95-CSORT | 0.5020 | Best cluster-token regularization | Current ceiling |
  | M157-PMD | 0.4990 | Aligned delivered point context | Alignment contributes, but is insufficient |
  | M161-MQF | 0.4920 | Aligned prior-mask foreground retrieval | Plain semantic retrieval failed |
  | M162-MQF-SH | 0.4980 | Equal-distribution shuffled-mask control | Generic scene/distribution component is strong |
  | M163-MQC | 0.4840 running | Foreground-minus-background contrast | Different object/scene contrast axis |
  | M166-MPF | launched | Reciprocal query-to-point feedback | Startup verification pending |

## 4. Gap Analysis
  - M161 and M162 use identical recurrent capacity and projections; only point
    alignment differs.
  - Because M162 exceeds M161 by 0.0060, adding aligned foreground context directly
    is not isolating object-specific information.
  - The existing variants do not subtract a same-histogram counterfactual from the
    aligned retrieval. M163 subtracts geometric background, not a distribution-
    matched permutation of the same predicted mask.
  - M166 launch reduced waiting from six to five, requiring one new structural
    experiment under the capacity+1 rule.

## 5. Design Rationale
  - M170-MQR computes two contexts from the same prior mask probabilities:
    aligned point context and a deterministic within-scene rolled counterfactual.
  - The query receives aligned minus counterfactual context.
  - This preserves mask histogram, query confidence, point count, and projection
    capacity while removing the scene/distribution component shared with M162.
  - Success would show that object-specific residual context exists but must be
    contrastively isolated; failure would close the M161/M162 semantic branch.
  - Complexity remains O(BQN), with no threshold, coefficient, schedule change,
    gate, new loss weight, or N^2 attention.

## 6. Next Batch
  -> pipeline/designs/exp_design_20260903-2013.md
================================================================================
