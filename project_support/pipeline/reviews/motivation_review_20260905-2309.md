================================================================================
  Motivation Review — cluster_project
  2026-09-05 23:09:39
================================================================================

## 1. Goal
  - goal.json target: mIoU >=0.5100 on ScanRefer.
  - Baseline model_base1=0.4894; champion M95=0.5020; gap=+0.0080.
  - Motivation: multi-scale cluster context improves grounding while explicit
    routing is harmful.
  - Constraints: Phase 1 structural mechanisms only; seed=1999; schedule and
    losses unchanged; FLOPs <=10.0G; no N^2 attention; obey all banned directions.

## 2. Story Status
  | Hypothesis | Status | Evidence | Gap |
  |------------|--------|----------|-----|
  | Multi-scale context helps | confirmed | A1=0.5012 vs baseline=0.4894 | Need robust improvement |
  | Generic distribution contaminates aligned retrieval | supported | M170=0.4970 vs M161=0.4920 | Below champion |
  | One coherent hierarchy branch helps | promising | M169 running best=0.5000 | Fine-only selection may be inconsistent |
  | Cross-scale hierarchy consistency helps | testing | M174-M176 waiting | Hard consistent branch untested |

## 3. Experiment Assessment
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M161-MQF | 0.4920 | Direct aligned mask context | Plain alignment is weak |
  | M162-MQF-SH | 0.4980 | Shuffled control | Generic distribution component is strong |
  | M170-MQR | 0.4970 | Factual minus rolled counterfactual | Object-specific residual is effective |
  | M169-MQB | running 0.5000 | Select branch by fine occupancy | Strongest active hierarchy result |
  | M174-MQHC | waiting | Soft minimum occupancy across levels | Point-level consistency pending |
  | M175-MQHF | waiting | Coarse-to-fine occupancy flow | Boundary change pending |
  | M176-MQSD | waiting | Sibling-relative occupancy | Local hierarchy competition pending |

## 4. Gap Analysis
  - M169 selects the highest-occupancy fine cluster and accepts its ancestors
    without checking whether the same branch remains supported at coarser levels.
  - A fine local peak can belong to a medium/coarse region with weak query support.
  - No queued variant selects one hard branch using a bottleneck score across the
    entire fine-to-coarse path.
  - M170 early stop and M171 launch reduced waiting from six to five.

## 5. Design Rationale
  - M177-MQBC computes occupancy at fine, medium, and coarse levels for every
    fine branch, takes the minimum along each complete path, and selects the
    branch with the strongest bottleneck score.
  - Success would show that hard branch coherence, not merely a fine-level peak,
    drives M169's gain; failure would favor M169's simpler local selection.
  - No threshold, learned scalar, loss weight, or schedule change is introduced.

## 6. Next Batch
  -> pipeline/designs/exp_design_20260905-2309.md
================================================================================
