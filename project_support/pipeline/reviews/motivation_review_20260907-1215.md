================================================================================
  Motivation Review — cluster_project
  2026-09-07 12:15:21
================================================================================

## 1. Goal
  - Description: cluster: multi-scale cluster context aggregates point-cloud
    features and writes context back into instance features; explicit routing
    is disproven, so the target is useful context rather than routing.
  - Target: ScanRefer mIoU >=0.5100.
  - Baseline: model_base1=0.4894.
  - Champion: M95-CTF-HCG-CSORT=0.5020; gap=+0.0080.
  - Constraints: FLOPs <=10.0G; unchanged schedule and losses; seed 1999;
    structural Phase 1 changes only; no N^2 attention.
  - Banned: gates, language routing, generic attention-pool variants, pruning,
    nomask, repeated injection, large projections, numeric tuning, explicit
    routing injection, and residual-message families.

## 2. Story Status
  | Hypothesis | Status | Evidence | Gap |
  |------------|--------|----------|-----|
  | Multi-scale context helps | confirmed | A1=0.5012 vs baseline=0.4894 | Need robust target-reaching mechanism |
  | One coherent hierarchy path helps | supported | M169=0.5000 | Hard one-path selection may discard uncertainty or parts |
  | Generic hierarchy occupancy helps | rejected | M165=0.4911 | Topology, not scale averaging, carries value |
  | Local inconsistency or query competition helps | rejected | M171=0.4936; M173=0.4921 | Both below hierarchy branch |
  | Alternative hierarchy topology improves retrieval | testing | M174-M179 running/waiting | Soft paths and frontier coverage untested |

## 3. Experiment Assessment
  | Experiment | mIoU | Relation To Motivation | Story Contribution |
  |------------|------|------------------------|--------------------|
  | M169-MQB | 0.5000 | One fine cluster plus ancestors | Strongest completed retrieval mechanism |
  | M172-MQS | 0.4966 | Stable decoder support | Persistence helps but loses detail |
  | M164-MQU | 0.4950 | Uncertainty retrieval | Boundary evidence is secondary |
  | M165-MQH | 0.4911 | Generic hierarchy occupancy | Rejects indiscriminate scale averaging |
  | M171-MQCC | 0.4936 | Query competition | Direct query competition is weak |
  | M173-MQCI | 0.4921 | Cluster inconsistency | Inconsistency is weak |
  | M174-M179 | running/waiting | Hierarchy topology variants | Active evidence collection |

## 4. Gap Analysis
  - M169 validates a coherent path but uses one hard fine-cluster decision.
  - M177/M178 test alternative hard single-path decisions; M179 tests a full
    subtree after one coarse decision.
  - No queued experiment computes a soft posterior over complete paths.
  - No queued experiment transports parent probability mass to children as a
    hierarchy-consistent distribution.
  - No queued experiment covers multiple medium object parts while selecting
    one representative fine cluster per part.
  - Waiting depth is 3 against a required reserve of 6.

## 5. Design Rationale
  - M180-MQPP multiplies occupancies along each fine-to-coarse path and pools
    under the normalized path posterior.
  - M181-MQHT transports coarse probability mass down the tree, conditioned
    by child occupancy at each level.
  - M182-MQFC selects one coarse region, preserves its medium-level coverage,
    and chooses one fine representative per medium branch.
  - Each mechanism changes retrieval topology without thresholds, learned
    coefficients, loss changes, schedule changes, or parameter sweeps.

## 6. Next Batch
  -> pipeline/designs/exp_design_20260907-1215.md
================================================================================
