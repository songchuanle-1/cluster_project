================================================================================
  Motivation Review — cluster_project
  2026-08-02 06:03:28
================================================================================

## 1. Goal
  - Target: mIoU >= 0.5100 | Champion: posA_l1 0.5012 | Gap: +0.0088 | Phase: 1 (NOT YET)
  - goal.json description: multi-scale cluster context mechanism — cluster bank aggregates point cloud features -> cluster_attn writes multi-scale context back to update inst_feats -> improve localization accuracy
  - Routing refuted (A3=0.4468, -0.0544), context-only confirmed effective (+0.0118)
  - Constraints active: FLOPs<=10G, no hyperparam tuning, no N^2-attention, no gate-series, no routing-series, no residual-series
  - Phase 0.5: goal.json has no active retention clause; decisions/_index.md last 10 entries have no question -> autonomous design allowed

## 2. Story Status
  | Hypothesis | Status | Evidence | Gap |
  |------|------|------|------|
  | Multi-scale cluster context improves localization | confirmed | champion=0.5012 vs base=0.4894 (gamma=+0.0118) | Need ablation of each design choice |
  | C2F routing contributes to performance | refuted | DRP(no routing)=0.5012 = champion; true_route=0.4468 | — |
  | Readback mechanism is current bottleneck | partial | DRP/ORT/CTF all ~0.5012; multiple token refinement paths hit same ceiling | Need to verify: what property of readback limits further improvement |
  | Nonlinear/conditional readback can break bottleneck | untested | All existing variants use linear/additive readback (feat+=gate*msg) | To be verified |

## 3. Experiment Assessment (motivation perspective)
  | Experiment | mIoU | Relation to motivation | Story contribution |
  |------------|------|-------------|-------------|
  | champion (posA_l1) | 0.5012 | Directly validates context writeback mechanism | Confirms core hypothesis |
  | M32-DRP | 0.5012 | Removes routing dead code, pure context | Proves routing unnecessary, DRP should be new baseline |
  | M17-ORT | 0.5005 | Orthogonal regularization of cluster tokens | Near champion, token diversity helps but not critical |
  | M41-CTF | 0.4995 | Per-token FFN refinement | Token quality improvement works but cannot break ceiling |
  | M45-NCR | 0.4980 | Soft attention assignment for readback | Close but not surpassing, approaching early-stop (7/10) |
  | M42-WCA | 0.4890 | Learned weight aggregation | Failed learned-weight pattern (3rd instance, after gate series) |
  | M38-FLM | 0.4865 | Feature-level linear modulation | Linear modulation insufficient |
  | M39-C2C | 0.4865 | Cluster-to-cluster attention | Inter-cluster token interaction brings no gain |
  | M16-CSR | 0.4875 | Spatial reweighting | Spatial attention in readback ineffective |

  Key pattern:
  (a) All experiments hitting ~0.5012 ceiling (DRP/ORT/CTF/champion) use the same additive readback: feat += gate * W(msg)
  (b) Experiments deviating from additive readback (WCA/FLM/C2C/CSR) all fall below 0.50
  (c) NCR uses soft attention readback, still running but already at 0.4980 plateau
  (d) Waiting: FILM (affine FiLM, gamma/beta) and SHC (split-head) still exploring readback variants

## 4. Gap Analysis (Q1: what does the story lack?)
  - Verified: context mechanism works (+0.0118), routing unnecessary, token refinement helps but not breakthrough
  - Unverified:
    (a) Should the interaction between point features and cluster message be symmetric/conditional? (current: cluster_msg -> Linear -> add, unidirectional and unconditional)
    (b) Does the cluster message -> point feature mapping need nonlinear transformation? (current: purely linear)
    (c) Should different points receive different readback based on their own feature state? (current: all points receive same msg*W, only gate scalar differs)
  - Contradictions/questions: Why cannot token refinement (ORT/CTF) or readback variants (NCR) break 0.5012 ceiling? Bottleneck likely not in token quality but in readback expressiveness.

## 5. Design Rationale (Q2+Q3: why these variants?)

  ### M48-BIL: Bilinear Readback
  - Fills gap: Unverified hypothesis (c) — point-conditional readback
  - Mechanism: feat += gate * (W1(feat) * W2(cluster_msg)) — bilinear interaction
  - Causal hypothesis: Different points (foreground/background/boundary) should receive different context updates. Bilinear interaction allows readback to depend on the point's own feature state.
  - Expected: > champion (0.5012) means conditionality is key; < baseline means conditionality introduces noise
  - Story advancement: Validates "readback should be point-conditional" hypothesis

  ### M49-NLR: Nonlinear Readback
  - Fills gap: Unverified hypothesis (b) — nonlinear readback mapping
  - Mechanism: feat += gate * MLP(cluster_msg) where MLP = Linear(d,4d)->ReLU->Linear(4d,d), hidden expansion 4x
  - Causal hypothesis: The cluster context -> point feature mapping may require nonlinear transformation. Simple Linear(d,d) may be unable to capture interactions between cluster message dimensions.
  - Expected: > champion means nonlinearity is key; ~champion means linear sufficient; < champion means nonlinear overfitting
  - Story advancement: Distinguishes "token quality bottleneck" vs "readback expressiveness bottleneck"

  ### Why not other directions
  - Cluster token self-attention (CSA): Requires deep modification of hier_postprocess.py, overlaps with M39-C2C=0.4865, high risk
  - Instance-level conditioning: Few parameters, likely triggers smell check, close to gate series
  - Cross-scale readback mixing: Overlaps with running M44-CSF (cross-scale fusion)
  - Channel grouping / conv1d readback: Close to smell #2

## 6. Next Batch
  -> See pipeline/designs/exp_design_20260802-060328.md
================================================================================