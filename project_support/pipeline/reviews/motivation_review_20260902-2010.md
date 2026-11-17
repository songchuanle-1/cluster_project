================================================================================
  Motivation Review — cluster_project
  2026-09-02 20:10:07
================================================================================

## 1. Goal
  - goal.json metric: mIoU >= 0.5100 on ScanRefer.
  - description: multi-scale cluster context is aggregated into a cluster bank and
    written back to instance features; explicit routing is disproven and context is
    the supported mechanism.
  - baseline: model_base1=0.4894.
  - champion: M95-CTF-HCG-CSORT=0.5020.
  - gap: +0.0080 to target.
  - constraints: <=10.0G FLOPs; unchanged schedule; Phase 1 structural mechanisms
    only; seed 1999 for structural screening; no N^2 point attention.
  - banned directions: gates, language routing, pooling/parameter sweeps, repeated
    3/4/6-layer injection, large Q/K/V/O stacks, explicit routing, residual message
    family, and numeric tuning.

## 2. Story Status
  | Hypothesis | Status | Evidence | Gap |
  |------------|--------|----------|-----|
  | Multi-scale cluster context improves grounding | confirmed | A1=0.5012 vs baseline=0.4894 | Need a robust path beyond 0.5020 |
  | Explicit routing improves context delivery | disproven | A3 true_route=0.4468 | Closed |
  | CSORT breaks the plateau robustly | partial/seed-fragile | M95=0.5020; controls near 0.490-0.494 | No stable gain |
  | Receiver message alignment matters | confirmed but insufficient | M157=0.4990 vs shuffled M158=0.4950 | Both below champion |
  | Direct geometric token enrichment helps | disproven | M159=0.4840 | M160 control still running |
  | Previous masks retrieve object-specific context | testing | M161 launched; M162-M166 queued | Existing batch treats each query mostly independently |
  | Competition between overlapping query masks identifies exclusive object support | untested | Multiple decoder queries can claim the same points; no current variant removes rival ownership | Primary next gap |
  | Changes between consecutive masks identify correction context | untested | Current variants use one previous mask snapshot | Alternative temporal gap |
  | A dominant hierarchy branch is better than averaging all occupied clusters | untested | M165 averages occupancy across hierarchy | Alternative structural gap |

## 3. Experiment Assessment
  | Experiment | mIoU | Relation to motivation | Story contribution |
  |------------|------|------------------------|--------------------|
  | M95-CSORT | 0.5020 | Best token regularization result | Current ceiling, seed-fragile |
  | M153-CSORT-MFP | 0.5000 | Combines token objectives | Objectives overlap; no stacking |
  | M157-PMD | 0.4990 | Aligned delivered context | Alignment helps but is insufficient |
  | M158-PMD-SH | 0.4950 | Shuffled alignment control | Confirms a 0.0040 alignment effect |
  | M159-GEO | 0.4840 | Direct geometry injection | Harmful; geometry-content branch closed |
  | M160-GEO-SH | running | Geometry content control | Too early for a conclusion |
  | M161-MQF | running | Prior-mask foreground retrieval | First prediction-conditioned test |
  | M162-M166 | waiting | Controls and alternative retrieval paths | Cover single-query weighting and reciprocal feedback |

## 4. Gap Analysis
  - Confirmed: context and semantic alignment matter, but unconditional access and
    additional token transformations do not exceed the champion.
  - Current batch gap: M161-M166 condition retrieval on each query's own previous
    mask, but do not explicitly resolve points claimed by multiple queries.
  - Temporal gap: no variant uses the direction of mask change between decoder layers
    to isolate where correction is occurring.
  - Hierarchy gap: M165 retrieves all occupied hierarchy levels; no variant tests
    whether one coherent parent-child branch should define object context.
  - Queue depth is 5 after M161 launch, equal to the contract capacity and below the
    required capacity+1 reserve, so one future experiment choice is required.

## 5. Design Rationale
  - Candidate A, exclusive query ownership: normalize support across queries at each
    point, then retrieve context from support owned by one query rather than shared
    foreground. This tests whether query collisions dilute object context.
  - Candidate B, mask-delta correction: retrieve signed context from points newly
    gained versus lost across two consecutive mask predictions. This tests whether
    the useful signal is correction direction rather than current support.
  - Candidate C, dominant hierarchy branch: select the maximum-occupancy cluster and
    its ancestor chain, then retrieve only that coherent branch. This tests whether
    averaging disconnected occupied clusters causes context dilution.
  - These candidates are mutually exclusive mechanisms for the single missing queue
    slot. None will be implemented before user selection.

## 6. Next Batch
  -> pipeline/designs/exp_design_20260902-2010.md
================================================================================
