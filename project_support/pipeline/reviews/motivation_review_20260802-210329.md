================================================================================
  Motivation Review — cluster_project
  2026-08-02 21:03:29
================================================================================

## 1. Goal
  - Target: mIoU >= 0.5100 | Champion: posA_l1 0.5012 | Gap: +0.0088 | Phase: 1 (NOT YET)
  - goal.json description: multi-scale cluster context mechanism — cluster bank aggregates point cloud features -> cluster_attn writes multi-scale context back to update inst_feats -> improve localization accuracy
  - Routing refuted (A3=0.4468), context-only confirmed (+0.0118). DRP ties champion (0.5012=0.5012).
  - Phase 0.5: goal.json has no active retention clause; recent decisions have no question type → autonomous design allowed

## 2. Story Status
  | Hypothesis | Status | Evidence | Gap |
  |------|------|------|------|
  | Multi-scale cluster context improves localization | confirmed | champion=0.5012 vs base=0.4894 (γ=+0.0118) | Need to break 0.5012 ceiling |
  | C2F routing contributes to performance | refuted | DRP(no routing)=0.5012 = champion | — |
  | Readback mechanism is current bottleneck | partial | DRP/ORT/CTF all ~0.5012; multiple paths hit same ceiling | Verify which readback property limits |
  | Point-conditional readback can break ceiling | testing | M48-BIL (waiting): bilinear interaction | Pending |
  | Nonlinear readback can break ceiling | testing | M49-NLR (waiting): MLP readback | Pending |
  | FiLM modulation can break ceiling | testing | M47-FILM (running): per-channel gamma/beta | Pending |
  | Adaptive dual-path readback can break ceiling | untested | M50-DGC (this batch) | To verify |

## 3. Experiment Assessment (motivation perspective)
  | Experiment | mIoU | Relation to motivation | Story contribution |
  |------------|------|-------------|-------------|
  | champion (posA_l1) | 0.5012 | Context writeback mechanism | Confirms core hypothesis ✓ |
  | M32-DRP | 0.5012 | Removes routing dead code | Proves routing unnecessary, DRP = new baseline |
  | M17-ORT | 0.5005 | Orthogonal regularization | Token diversity helps but not critical |
  | M41-CTF | 0.4995 | Per-token FFN refinement | Token quality ceiling at ~0.50 |
  | M45-NCR | 0.4980 | Soft attention assignment | Soft readback feasible but not superior |
  | M43-CLN | 0.4930 | Cluster LayerNorm | Pure normalization insufficient (smell hit) |
  | M42-WCA | 0.4890 | Learned weight aggregation | Failed (3rd learned-weight pattern) |
  | M44-CSF | 0.4917@ep16 | Cross-scale cluster fusion | Early, oscillating, not promising yet |

  Key pattern: All ceiling experiments use additive readback (feat += gate * transform(msg)).
  The bottleneck is in how cluster context gets written back to point features.
  Three hypotheses being tested in parallel:
    (a) Readback should be point-conditional (BIL)
    (b) Readback needs nonlinearity (NLR)
    (c) Readback should be per-channel modulated (FILM)
  Missing hypothesis: (d) Readback should adaptively balance cluster-context vs self-preservation based on how much the point already agrees with the cluster (DGC)

## 4. Gap Analysis (Q1: what does the story lack?)
  - Verified: context mechanism works (+0.0118), routing unnecessary, various token refinement paths hit ~0.5012
  - Unverified:
    (a) Point-conditionality matters (M48-BIL pending)
    (b) Nonlinearity in readback matters (M49-NLR pending)
    (c) Per-channel modulation matters (M47-FILM running)
    (d) Adaptive dual-path (cluster-context vs self-preservation) matters (M50-DGC this batch)
  - Contradictions: All ceiling-hitting experiments use the same additive pattern. Is 0.5012 a fundamental limit of single-path additive readback?

## 5. Design Rationale (Q2+Q3: why M50-DGC?)

  ### M50-DGC: Difference-Gated Context
  - Fills gap: Unverified hypothesis (d) — adaptive dual-path readback
  - Mechanism: 
    1. Compute difference signal: diff = point_feat - cluster_msg
    2. Gate from difference: gate = sigmoid(Linear(diff, 1))
    3. Dual-path update: feat += gate * W_c(cluster_msg) + (1-gate) * W_s(point_feat)
  - Causal hypothesis: Boundary/outlier points whose features disagree with cluster context should preserve their own fine-grained information while receiving cluster context. Interior points that already agree should be more influenced by cluster context. The difference-based gate implements this adaptive trade-off.
  - Expected: > champion (0.5012) means adaptive dual-path breaks ceiling; ~champion means adaptive mechanism doesn't matter beyond basic additive readback; < champion means the dual-path introduces harmful interference.
  - Story advancement: Distinguishes "readback expressiveness ceiling" from "single-path vs dual-path" hypothesis.
  - Why this direction vs alternatives:
    - NOT overlapped by FILM (per-channel modulation, no dual-path)
    - NOT overlapped by BIL (point-conditional multiplicative, no self-preservation path)
    - NOT overlapped by NLR (nonlinear transform, no adaptive gate)
    - Differs from gate-series (cag/cfe/layerscale) which are pure learned weights without structural computation graphs

## 6. Next Batch
  → See pipeline/designs/exp_design_20260802-210329.md
================================================================================
