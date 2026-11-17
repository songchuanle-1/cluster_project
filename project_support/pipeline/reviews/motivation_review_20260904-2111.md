================================================================================
  Motivation Review — cluster_project
  2026-09-04 21:11:00
================================================================================

## 1. Goal
  - Target mIoU >=0.5100; champion M95=0.5020; gap=+0.0080.
  - Motivation: multi-scale cluster context improves grounding; explicit routing
    is harmful.
  - Constraints: structural mechanisms only, unchanged seed/schedule/losses,
    FLOPs <=10.0G, no N^2 attention, and all goal.json bans.

## 2. Story Status
  | Hypothesis | Status | Evidence | Gap |
  |------------|--------|----------|-----|
  | Multi-scale context helps | confirmed | A1=0.5012 vs baseline=0.4894 | Need robust improvement |
  | Direct geometry helps | disproven | M159=0.4840; M160 shuffled=0.4910 | Axis closed |
  | Hierarchical mask support helps | testing | M165 launched; M169/M173 waiting | Cross-scale agreement untested |

## 3. Experiment Assessment
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M159-GEO | 0.4840 | Aligned geometric enrichment | Geometry content is harmful |
  | M160-GEO-SH | 0.4910 | Shuffled geometry control | Injection shell is neutral |
  | M165-MQH | running | Averages occupancy-weighted hierarchy tokens | Tests soft hierarchy token retrieval |
  | M169-MQB | waiting | Selects one dominant ancestor branch | Tests hard hierarchy coherence |
  | M173-MQCI | waiting | Retrieves point-cluster disagreement | Tests local inconsistency |

## 4. Gap Analysis
  - Existing hierarchy variants either average tokens, select one hard branch, or
    focus on disagreement.
  - None asks whether a point should contribute only when its query support is
    consistent at fine, medium, and coarse hierarchy levels.
  - M165 launch reduced waiting from six to five, requiring one structural refill.

## 5. Design Rationale
  - M174-MQHC computes query occupancy for every cluster level, broadcasts each
    occupancy to points, and uses the minimum across scales as the retrieval weight.
  - The minimum is a parameter-free logical consensus: one weak hierarchy level
    suppresses a point that lacks coherent multi-scale support.
  - Success supports cross-scale consensus; failure closes the remaining soft
    hierarchy-consistency direction.

## 6. Next Batch
  -> pipeline/designs/exp_design_20260904-2111.md
================================================================================
