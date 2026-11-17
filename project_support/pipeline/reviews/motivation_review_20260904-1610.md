================================================================================
  Motivation Review — cluster_project
  2026-09-04 16:10:00
================================================================================

## 1. Goal
  - goal.json metric: mIoU >= 0.5100 on ScanRefer.
  - description: multi-scale cluster context is aggregated into a cluster bank and
    written back to instance features; explicit routing is disproven and context is
    the supported mechanism.
  - baseline: model_base1=0.4894.
  - champion: M95-CTF-HCG-CSORT=0.5020.
  - gap: +0.0080 to target.
  - constraints: FLOPs <=10.0G; unchanged seed/schedule/losses; Phase 1 structural
    mechanisms only; no N^2 point attention; all banned directions remain active.

## 2. Story Status
  | Hypothesis | Status | Evidence | Gap |
  |------------|--------|----------|-----|
  | Multi-scale cluster context improves grounding | confirmed | A1=0.5012 vs baseline=0.4894 | Need robust improvement beyond 0.5020 |
  | Explicit routing improves delivery | disproven | A3=0.4468 | Closed |
  | Generic recurrent context helps | partial | M162 shuffled=0.4980 > M161 aligned=0.4920 | Below champion; semantic alignment is not sufficient |
  | Foreground/background contrast helps | disproven | M163=0.4899 | Closed |
  | Reciprocal query-to-point feedback helps | disproven | M166=0.4899 | Closed |
  | Query competition, temporal stability, and cluster consistency identify useful context | untested | M167/M168 cover related but distinct paths | Current structural gap |

## 3. Experiment Assessment
  | Experiment | mIoU | Relation to motivation | Story contribution |
  |------------|------|------------------------|--------------------|
  | M95-CSORT | 0.5020 | Best cluster-token result | Current ceiling, seed-fragile |
  | M162-MQF-SH | 0.4980 | Shuffled recurrent context | Generic context helps more than aligned foreground |
  | M163-MQC | 0.4899 | Foreground-minus-background query contrast | Object/scene subtraction fails |
  | M166-MPF | 0.4899 | Query-to-point reciprocal feedback | Reciprocal direction fails |
  | M122-MLAY-S123 | 0.4940 | Multi-layer platform seed control | MLay seed peak is not robust |
  | M167-MQX | running | Point ownership competition | Early structural screen |
  | M168-MQD | running | Signed temporal change | Early structural screen |
  | M164-MQU | running | Uncertainty-focused retrieval | No validation result yet |

## 4. Gap Analysis
  - Existing MQX suppresses shared point ownership but does not explicitly subtract
    the context retrieved by rival queries.
  - Existing MQD focuses on newly gained/lost support but does not test the stable
    intersection that persists across decoder layers.
  - Existing MQH/MQB use cluster occupancy but do not retrieve the point context
    that disagrees with its own fine-cluster mean occupancy.
  - waiting=3 is below the required six-task reserve, so three structural variants
    are required.

## 5. Design Rationale
  - M171-MQCC: retrieve each query's mask-weighted context and subtract the
    mask-weighted context of all rival queries. This tests direct context
    contamination between competing hypotheses.
  - M172-MQS: retrieve context from the soft intersection of two consecutive mask
    predictions. This tests whether persistent object core is more reliable than
    transient correction regions.
  - M173-MQCI: compute fine-cluster mean mask probability, broadcast it to points,
    and retrieve point context weighted by absolute point-vs-cluster disagreement.
    This tests whether errors concentrate at cluster-inconsistent support.
  - Success advances a distinct causal story for each mechanism; failure closes
    competition, stable-core, or cluster-consistency retrieval respectively.

## 6. Next Batch
  -> pipeline/designs/exp_design_20260904-1610.md
================================================================================
