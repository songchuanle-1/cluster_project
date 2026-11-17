================================================================================
  Motivation Review — cluster_project
  2026-09-06 14:37:12
================================================================================

## 1. Goal
  - Description: multi-scale cluster context aggregates point-cloud features
    and writes context back into instance features; explicit routing has been
    disproven, so the target mechanism is context rather than routing.
  - Target: ScanRefer mIoU >=0.5100.
  - Baseline: model_base1=0.4894.
  - Champion: M95-CTF-HCG-CSORT=0.5020; remaining gap=+0.0080.
  - Constraints: FLOPs <=10.0G; unchanged schedule and losses; structural seed
    1999; Phase 1 structural mechanisms only; no N^2 attention.
  - Banned directions: gates, language routing, attention-pool/qcond/agg/multi,
    prune, nomask, repeated 3/4/6-layer injection, large projections, numeric
    tuning, explicit routing injection, and residual-message families.

## 2. Story Status
  | Hypothesis | Status | Evidence | Gap |
  |------------|--------|----------|-----|
  | Multi-scale context helps | confirmed | A1=0.5012 vs baseline=0.4894 | Need robust target-reaching mechanism |
  | Stable decoder support helps | supported but limited | M172=0.4966 | Below hierarchy branch |
  | One coherent hierarchy path helps | supported | M169=0.5000 | Single path may omit object parts |
  | Full hierarchy consistency helps | testing | M174/M177/M178 waiting | Whole-subtree aggregation untested |

## 3. Experiment Assessment
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M169-MQB | 0.5000 | Fine peak plus ancestor path | Strongest completed prediction-conditioned retrieval |
  | M170-MQR | 0.4970 | Factual minus counterfactual context | Generic scene context contamination is real |
  | M172-MQS | 0.4966 | Consecutive-mask stable core | Persistence helps but loses useful detail |
  | M174-MQHC | waiting | Soft all-level consensus | Tests hierarchy-wide agreement |
  | M177-MQBC | waiting | Full-path bottleneck selection | Tests coherent single-path selection |
  | M178-MQTD | waiting | Hard top-down descent | Tests coarse-constrained single-path selection |

## 4. Gap Analysis
  - M169 and M178 retrieve one fine-to-coarse path per query.
  - A ScanRefer object can span multiple fine and medium clusters; selecting a
    single descendant can discard complementary parts after the correct coarse
    object region has already been localized.
  - No queued experiment selects one coarse object region while retaining and
    aggregating all of its descendants according to predicted occupancy.
  - M172 terminated and M173 launched, reducing waiting depth from six to five.

## 5. Design Rationale
  - M179-MQST selects the highest-occupancy coarse cluster with a hard forward,
    straight-through selector.
  - At finer levels it preserves the complete selected subtree and normalizes
    predicted occupancies only among descendants of that coarse region.
  - Success would show that coarse localization should constrain context while
    retaining multi-part evidence; failure would favor single-path retrieval.
  - The mechanism changes candidate topology and information aggregation, with
    no threshold, temperature, new coefficient, or schedule change.

## 6. Next Batch
  -> pipeline/designs/exp_design_20260906-1437.md
================================================================================
