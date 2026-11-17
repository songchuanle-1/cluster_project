================================================================================
  Motivation Review — cluster_project
  2026-09-05 07:10:25
================================================================================

## 1. Goal
  - goal.json: target mIoU >=0.5100 on ScanRefer; baseline model_base1=0.4894.
  - Champion M95-CTF-HCG-CSORT=0.5020; remaining gap=+0.0080.
  - Motivation: multi-scale cluster context improves grounding while explicit
    routing is harmful.
  - Constraints: structural mechanisms only in Phase 1; seed=1999; unchanged
    schedule/losses; FLOPs <=10.0G; no N^2 attention; obey all banned directions.

## 2. Story Status
  | Hypothesis | Status | Evidence | Gap |
  |------------|--------|----------|-----|
  | Multi-scale context helps | confirmed | A1=0.5012 vs baseline=0.4894 | Need robust improvement |
  | Decoder-time mask changes help | disproven | M168-MQD=0.4900 | Temporal delta closed |
  | Query collision harms retrieval | disproven | M167-MQX=0.4910 | Exclusive ownership closed |
  | Hierarchy structure identifies object support | testing | M169 running; M173-M175 waiting | Sibling discrimination untested |

## 3. Experiment Assessment
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M162-MQF-SH | 0.4980 | Shuffled retrieval control | Distribution context remains strongest retrieval result |
  | M167-MQX | 0.4910 | Exclusive query ownership | Query collision closed |
  | M168-MQD | 0.4900 | Decoder-time support delta | Temporal correction closed |
  | M169-MQB | running | One dominant hierarchy branch | Hard hierarchy coherence under test |
  | M174-MQHC | waiting | Minimum all-scale occupancy | Static hierarchy consensus under test |
  | M175-MQHF | waiting | Coarse-to-fine occupancy flow | Hierarchy refinement change under test |

## 4. Gap Analysis
  - Existing hierarchy variants compare levels over the same point or choose one
    dominant branch, but none compares competing child clusters under the same
    parent region.
  - A parent cluster can have high query occupancy because it mixes target and
    distractor children; sibling-relative evidence can isolate the distinctive child.
  - M168 early stop freed GPU1 and M170 launched, reducing waiting from six to five.

## 5. Design Rationale
  - M176-MQSD computes query occupancy for child clusters at fine and medium
    levels, subtracts the mean occupancy of other siblings sharing the same
    parent, and retrieves points from positive sibling-relative evidence.
  - Parents with only one child contribute zero, avoiding unsupported contrast.
  - Success would show that local competition inside hierarchy parents isolates
    object evidence; failure would close sibling-discrimination retrieval.

## 6. Next Batch
  -> pipeline/designs/exp_design_20260905-0710.md
================================================================================
