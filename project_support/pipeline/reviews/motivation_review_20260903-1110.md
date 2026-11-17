================================================================================
  Motivation Review — cluster_project
  2026-09-03 11:10:00
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
    only; seed 1999; no N^2 point attention.

## 2. Story Status
  | Hypothesis | Status | Evidence | Gap |
  |------------|--------|----------|-----|
  | Multi-scale cluster context improves grounding | confirmed | A1=0.5012 vs baseline=0.4894 | Need robust improvement beyond 0.5020 |
  | Static prior-mask foreground retrieval helps | failed | M161=0.4920 at 26/50 | Plain foreground branch closed |
  | Mask semantic alignment matters | testing | M162 shuffled control running | Await paired result |
  | Foreground/background contrast helps | testing | M163 launched | Await result |
  | Averaging all occupied hierarchy tokens dilutes object context | untested | M165 averages occupancy-weighted context across all levels/clusters | Primary remaining hierarchy gap |

## 3. Experiment Assessment
  | Experiment | mIoU | Relation to motivation | Story contribution |
  |------------|------|------------------------|--------------------|
  | M95-CSORT | 0.5020 | Best cluster-token regularization | Current ceiling |
  | M157-PMD | 0.4990 | Aligned receiver context | Alignment helps but is insufficient |
  | M159-GEO | 0.4840 | Direct geometry injection | Geometry content is harmful |
  | M161-MQF | 0.4920 | Static foreground retrieval | Fails to break context dilution |
  | M162-MQF-SH | running | Semantic control | Tests alignment versus capacity |
  | M163-MQC | running | Foreground/background contrast | Tests discriminative retrieval |
  | M164-M168 | waiting | Other prediction-conditioned mechanisms | Cover uncertainty, hierarchy average, reciprocal, ownership, and temporal delta |

## 4. Gap Analysis
  - M165 uses soft occupancy over every cluster at every hierarchy level and averages
    all resulting contexts.
  - If a query mask spans disconnected regions, this operation can mix several
    incompatible branches into one query update.
  - The hierarchy already provides deterministic fine-to-coarse parent maps, so a
    coherent object path can be selected without introducing new coordinates,
    attention projections, thresholds, or tuning coefficients.
  - M163 launch reduced waiting depth from six to five, requiring one new experiment.

## 5. Design Rationale
  - M169-MQB computes fine-cluster occupancy from the prior query mask.
  - It selects the maximum-occupancy fine cluster for each query.
  - It follows the existing parent maps and retrieves exactly one token at each
    hierarchy level along the selected branch.
  - The branch tokens are averaged into a coherent multi-scale context.
  - Success would identify disconnected hierarchy mixing as the bottleneck; failure
    would close the remaining hierarchy-selection direction.

## 6. Next Batch
  -> pipeline/designs/exp_design_20260903-1110.md
================================================================================
