================================================================================
  Motivation Review — cluster_project
  2026-09-05 06:12:25
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
  | Query collision harms retrieval | disproven | M167-MQX=0.4910 | Exclusive ownership closed |
  | Hierarchy structure identifies object support | testing | M165 running; M169 launched; M173/M174 waiting | Cross-scale change untested |
  | Mask alignment is sufficient | disproven | M162 shuffled=0.4980 > M161 aligned=0.4920 | Need structural rather than plain semantic selection |

## 3. Experiment Assessment
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M161-MQF | 0.4920 | Aligned foreground retrieval | Plain mask semantics are weak |
  | M162-MQF-SH | 0.4980 | Shuffled control | Generic distribution context dominates |
  | M167-MQX | 0.4910 | Exclusive query ownership | Query collision branch closed |
  | M168-MQD | running 0.4900 | Decoder-time support change | Temporal correction under test |
  | M169-MQB | launched | Hard dominant hierarchy branch | Hierarchy coherence under test |
  | M173-MQCI | waiting | Point versus fine-cluster disagreement | Local inconsistency under test |
  | M174-MQHC | waiting | Minimum cross-scale occupancy | Static hierarchy consensus under test |

## 4. Gap Analysis
  - Existing hierarchy variants test averaged occupancy, one hard branch,
    point/fine disagreement, and static all-scale consensus.
  - None tests the information introduced or removed when a coarse region is
    refined into medium and fine clusters.
  - M167 early stop freed GPU0 and M169 launched, reducing waiting from six to
    five and triggering one structural reserve experiment.

## 5. Design Rationale
  - M175-MQHF broadcasts query occupancy from every hierarchy level to points.
  - For each adjacent coarse-to-fine pair, it retrieves newly gained support
    context minus support lost during refinement, then averages the pairwise
    flows.
  - Success would show that hierarchy boundaries carry discriminative context;
    failure would close cross-scale occupancy-change retrieval.
  - The mechanism is distinct from M168 decoder-time deltas, M173 point/fine
    disagreement, and M174 static minimum consensus.

## 6. Next Batch
  -> pipeline/designs/exp_design_20260905-0612.md
================================================================================
