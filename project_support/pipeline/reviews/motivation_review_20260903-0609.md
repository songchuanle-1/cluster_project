================================================================================
  Motivation Review — cluster_project
  2026-09-03 06:09:36
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
  - banned directions: gates, language routing, numeric sweeps, repeated 3/4/6-layer
    injection, large Q/K/V/O stacks, explicit routing, and residual message family.

## 2. Story Status
  | Hypothesis | Status | Evidence | Gap |
  |------------|--------|----------|-----|
  | Multi-scale cluster context improves grounding | confirmed | A1=0.5012 vs baseline=0.4894 | Need a robust path beyond 0.5020 |
  | Explicit routing improves delivery | disproven | A3=0.4468 | Closed |
  | Static foreground-mask retrieval helps | testing | M161=0.4880 at 19/50 | Below champion; still running |
  | Foreground semantic alignment matters | testing | M162 shuffled control launched | Await paired result |
  | Cross-layer mask changes identify correction direction | untested | Existing M161-M167 consume one previous mask state | Primary remaining temporal gap |

## 3. Experiment Assessment
  | Experiment | mIoU | Relation to motivation | Story contribution |
  |------------|------|------------------------|--------------------|
  | M95-CSORT | 0.5020 | Best token regularization result | Current ceiling, seed-fragile |
  | M157-PMD | 0.4990 | Aligned receiver context | Alignment matters but is insufficient |
  | M158-PMD-SH | 0.4950 | Shuffled control | Confirms 0.0040 alignment contribution |
  | M159-GEO | 0.4840 | Direct geometry injection | Harmful |
  | M161-MQF | 0.4880 running | Static prior-mask foreground retrieval | Near baseline, not yet competitive |
  | M162-MQF-SH | running | Static mask semantic control | Startup healthy |
  | M163-M167 | waiting | Alternative static/reciprocal prediction paths | Queue reserve before this tick was five |

## 4. Gap Analysis
  - Existing prediction-conditioned variants use the current previous-layer mask as
    a static support map.
  - They do not distinguish points newly acquired by a query from points it has
    abandoned between decoder layers.
  - A signed change signal can represent correction direction without a threshold,
    temperature, learned gate, or additional loss coefficient.
  - M162 launch reduced waiting depth from six to five, triggering one additional
    structural experiment under the capacity+1 rule.

## 5. Design Rationale
  - M168-MQD stores two consecutive decoder mask predictions.
  - Positive mask-probability change pools newly gained point context.
  - Negative change pools newly lost point context.
  - The query update uses gained context minus lost context before the next decoder.
  - Success would show that temporal correction direction is more informative than
    static foreground support; failure would close the deferred mask-delta branch.
  - Complexity remains O(BQN), using already materialized mask tensors.

## 6. Next Batch
  -> pipeline/designs/exp_design_20260903-0609.md
================================================================================
