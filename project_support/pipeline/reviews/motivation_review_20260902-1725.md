================================================================================
  Motivation Review — cluster_project
  2026-09-02 17:25:00
================================================================================

## 1. Goal
  - goal.json metric: mIoU >= 0.5100 on ScanRefer.
  - description: multi-scale cluster context is aggregated into a cluster bank and
    written back to instance features; routing itself is disproven and context is
    the supported mechanism.
  - baseline: model_base1=0.4894.
  - champion: M95-CTF-HCG-CSORT=0.5020.
  - gap: +0.0080 to target.
  - constraints: <=10.0G FLOPs; no schedule-only changes; Phase 1 allows only
    structural mechanisms; seed 1999 for structural screening; no N^2 attention.
  - banned directions: gates, language routing, aggregation/pooling sweeps, repeated
    3/4/6-layer injection, large Q/K/V/O projections, explicit routing, residual
    message family, and Phase 1 numeric tuning.

## 2. Story Status
  | Hypothesis | Status | Evidence | Gap |
  |------------|--------|----------|-----|
  | Multi-scale cluster context improves grounding | confirmed | A1 0.5012 vs baseline 0.4894, gamma=+0.0118 | Need a robust path beyond the 0.5020 ceiling |
  | Explicit routing improves the message | disproven | A3 true_route=0.4468 | Closed |
  | CSORT token decorrelation breaks the ceiling | partial/seed-fragile | M95=0.5020, other seeds 0.490-0.494 | No robust gain |
  | Changing CSORT scale/object/loss placement helps | disproven | M149-M157 all <=0.5000; M152/M156 isolated pairs 0.494/0.495 | Closed |
  | Adding geometric token content helps | disproven | M159-GEO=0.4840 | M160 shuffled control remains |
  | Decoder queries can use cluster context directly | prior implementations disproven | QMOD/DCA/DCM and combinations <=0.5010 | Previous methods were unconditional direct access, not prediction-conditioned retrieval |
  | Previous decoder masks can retrieve object-specific cluster context | untested | Decoder already produces BxQxN masks each layer; no experiment feeds this prediction back into the next query | Primary open structural gap |

## 3. Experiment Assessment
  | Experiment | mIoU | Relation to motivation | Story contribution |
  |------------|------|------------------------|--------------------|
  | M152-CSORT-F1 | 0.4940 | Isolates fine adjacent-scale CSORT | Fine pair alone is insufficient |
  | M153-CSORT-MFP | 0.5000 | Combines two token regularizers | Objectives overlap; no stacking |
  | M154-CSORT-GSC | 0.4930 | Adds scene-global cluster scale | Global context dilutes object-local signal |
  | M155-CSORT-RF | 0.4950 | Moves CSORT to refined tokens | Operand relocation fails |
  | M156-CSORT-CP | 0.4950 | Isolates coarse adjacent-scale CSORT | Coarse pair alone is insufficient |
  | M157-CSORT-PMD | 0.4990 | Moves decorrelation to delivered point messages | Viable but below champion |
  | M159-CSORT-GEO | 0.4840 | Injects centroid/radius into tokens | Geometry injection is harmful |

## 4. Gap Analysis
  - Confirmed: cluster tokens are necessary and context readback produces the main
    gain; explicit routing, extra token transforms, geometry, direct decoder access,
    and regularizer combinations do not break the plateau.
  - Missing: the decoder never uses its own current object hypothesis to retrieve
    object-specific context. Existing query-context experiments expose every query
    to generic cluster features, so irrelevant scene context can dominate.
  - Mechanistic question: can the previous layer's predicted mask serve as a sparse,
    object-conditioned retrieval key for the next query without N^2 attention?
  - Risk: seed-1999 peaks have been fragile. This batch is a structural screen only;
    any apparent gain must later receive seed controls.

## 5. Design Rationale
  - M161-MQF: use the previous soft foreground mask to pool current cluster-enhanced
    point features into the next query. Success would show that prediction-conditioned
    retrieval, rather than unconditional decoder access, is the missing path.
  - M162-MQF-SH: roll mask weights within each scene while preserving their histogram.
    MQF > MQF-SH would prove semantic alignment, not residual capacity, carries gain.
  - M163-MQC: retrieve foreground minus background context. This tests whether
    discrimination requires an explicit object-versus-scene contrast.
  - M164-MQU: retrieve high-uncertainty boundary context via 4p(1-p). This tests
    whether refinement should focus on ambiguous points instead of confident interiors.
  - M165-MQH: convert prior point masks into per-cluster occupancy across all hierarchy
    levels and retrieve cluster tokens directly. This tests whether the cluster
    bottleneck should be queried by predicted object support rather than broadcast
    back to every point.
  - M166-MPF: use previous mask logits to project each query back only onto its
    predicted support, updating point features before the next decoder. This tests
    the reciprocal direction of the same cycle: object hypotheses refine points,
    then refined points update queries.
  - After this batch: success identifies a new recurrent information path; failure
    closes prediction-conditioned retrieval and leaves the project at a documented
    architecture-space plateau pending M158/M160 controls.

## 6. Next Batch
  -> pipeline/designs/exp_design_20260902-1725.md (M161-M166)
================================================================================
