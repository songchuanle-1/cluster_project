================================================================================
  Motivation Review — cluster_project
  2026-09-06 00:11:08
================================================================================

## 1. Goal
  - goal.json target: mIoU >=0.5100 on ScanRefer.
  - Baseline model_base1=0.4894; champion M95=0.5020; gap=+0.0080.
  - Motivation: multi-scale cluster context improves grounding while explicit
    routing is harmful.
  - Constraints: structural mechanisms only; seed=1999; unchanged schedule and
    losses; FLOPs <=10.0G; no N^2 attention; obey all banned directions.

## 2. Story Status
  | Hypothesis | Status | Evidence | Gap |
  |------------|--------|----------|-----|
  | Multi-scale context helps | confirmed | A1=0.5012 vs baseline=0.4894 | Need robust improvement |
  | One coherent hierarchy branch helps | supported | M169=0.5000 | Selection direction untested |
  | Counterfactual residual helps | supported | M170=0.4970 | Below hierarchy branch |
  | Full-path branch coherence helps | testing | M177 waiting | Top-down conditional search untested |

## 3. Experiment Assessment
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M162-MQF-SH | 0.4980 | Shuffled mask retrieval | Strong distribution-context control |
  | M169-MQB | 0.5000 | Fine peak plus ancestor chain | Strongest active structural mechanism |
  | M170-MQR | 0.4970 | Factual minus counterfactual | Positive object-specific residual |
  | M174-MQHC | waiting | Soft all-level consistency | Point-level consensus pending |
  | M177-MQBC | waiting | Full-path bottleneck branch | Global branch scoring pending |

## 4. Gap Analysis
  - M169 starts from the largest fine-cluster occupancy and follows ancestors.
  - A local fine peak can occur inside the wrong coarse object region.
  - M177 scores all complete paths jointly, but no experiment performs explicit
    conditional search from coarse object region to medium and fine subregions.
  - M169 early stop and M172 launch reduced waiting from six to five.

## 5. Design Rationale
  - M178-MQTD selects the coarse cluster with highest query occupancy, then
    selects a medium child only within that coarse parent, then a fine child
    only within the selected medium parent.
  - Every stage uses hard forward selection with a coefficient-free
    straight-through gradient path.
  - Success would indicate that coarse object localization should constrain
    later detail selection; failure would favor M169 fine-first search.

## 6. Next Batch
  -> pipeline/designs/exp_design_20260906-0011.md
================================================================================
