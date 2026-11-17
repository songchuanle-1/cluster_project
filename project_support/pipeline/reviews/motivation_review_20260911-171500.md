================================================================================
  Motivation Review - cluster_project
  2026-09-11T17:15:00+08:00
================================================================================

## 1. Goal
Authoritative goal.json snapshot:

```json
{
  "metric": {"name": "mIoU", "target": 0.51, "dataset": "ScanRefer"},
  "baseline_experiment_id": "model_base1",
  "description": "cluster: target concrete ScanRefer 3D grounding errors, investigate a lightweight structural mechanism with core novelty, derivability, and falsifiability, target mIoU >= 0.51. Multi-scale cluster context is existing work and is no longer treated as a pooling, selector, readback-position, or variant-count research line. Diagnose candidate coverage/boundaries, same-category discrimination/relation binding, and multi-scale evidence duplication; select one main mechanism from evidence and cover matched controls, robustness/generalization, and efficiency. Shared-reference consistency is only a provisional candidate. Existing context/routing results are historical evidence, not validation of a new mechanism.",
  "findings": {
    "A0_baseline": "model_base1 = 0.4894 (no cluster)",
    "A1_context_only": "champion Lite = 0.5012 (multi-scale context written back by ID; routing computed but _cluster_to_points discarded -> effectively context-only)",
    "A3_routing_active": "TrueRoute = 0.4468 (routing index really affects messages) -> -0.0544 vs A1, active routing is harmful",
    "A4_shuffle_control": "structure/content control was part of the old line and does not promote a new mechanism",
    "D1_detail_relause": "D1-detail relaunch = 0.5003 at epoch 28; detail alone is close to champion but below it",
    "E4_res_detail_terminal": "E4 residual+detail = 0.4944; residual and detail have no demonstrated synergy"
  },
  "constraints": [
    "FLOPs <= 10.0G; peak memory +15% requires >= +0.003 mIoU",
    "No single-variant schedule changes before a unified correction",
    "Phase 1 structural changes only; no tuning, hyperparameter sweeps, pure numerical config variants, or <5K-parameter single-operator additions",
    "Stop a branch when improvement <0.002 and the plateau does not rise",
    "Context claim A1-A0 >=0.005 is confirmed at +0.0118; routing claim A3-A1 >=0.002 is falsified at -0.0544",
    "Convergence uses recent-validation plateau and 5 consecutive non-improvements; structural first screen uses seed 1999",
    "No N^2 attention; efficiency measured with warmup20/repeat100 median and P90",
    "Future research must cover error diagnosis, core mechanism/formula derivation, verified primary-source novelty, matched mechanism controls, generalization/robustness, and efficiency",
    "Every future core mechanism must state the concrete error and evidence, variables and hypotheses, stepwise goal/constraint-to-forward/loss derivation, gradients/degeneracies/complexity, difference from verified primary papers and historical local failures, matched controls, and preregistered rejection conditions",
    "Scientific admission takes priority over queue refill; no eligible candidate means continue diagnostics, derivation, primary-source verification, or offline correctness checks",
    "Oracle is diagnostic only; test data cannot select a mechanism; no automatic new dataset, annotation, multi-seed campaign, or automatic successor variants"
  ],
  "banned": [
    "gate family (cag/cfe/layerscale)",
    "language routing family (langroute/langc2f/scale)",
    "attnpool/qcond/agg/multi family",
    "prune before benchmark repair",
    "nomask expansion",
    "repeated 3/4/6-layer injection",
    "large Q/K/V/O projections",
    "Phase1 tuning family and the general tuning-smell rules",
    "true_route/explicit routing injection",
    "residual family after fixed-ceiling and no-synergy evidence"
  ]
}
```

Current checker status: Phase 1 NOT YET; baseline 0.4894, champion 0.5020,
target 0.5100, gap +0.0080. Waiting is 4 with actual capacity 4; no free
training slot. The next action therefore must improve scientific admission or
diagnostic certainty, not fill the queue with a renamed old variant.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Missing useful positive dominates M95 recoverable errors | not supported | 99/111 M95 recoverable banks contain a usable positive | Does not explain why useful candidates lose |
| Padding exposure explains selected ranking errors | not supported as a main effect | 42 real capture records, mean relative query-gradient change 1.536e-4 | Training-time causality remains unmeasured |
| Independent score gradients oppose bad rankings | supported only as an objective-level statement | 568 stored-gradient readbacks; all 84/99 H margins have negative independent velocity | JJ^T on actual heads and all losses were never measured |
| Baseline and M95 have the same discriminator-head ownership | false by source text, unverified by object identity | baseline add_module(shared) versus M95 per-layer Sequential | Actual object, parameter, storage, and checkpoint identities not yet audited |
| Shared head coupling is the main error cause | unsupported | no real head-input capture and no matched intervention | Must verify sharing contract before collecting features |
| Shared head coupling is a novel mechanism | not admissible | parameter tying and chain-rule coupling are standard | No primary-source novelty argument or minimal mechanism record |

## 3. Experiment Assessment
| Experiment or audit | Result | Motivation relation | Contribution |
|---|---|---|---|
| D1 expansion | baseline 0.535914 selected / 0.834246 oracle; M95 0.502217 / 0.848108 | Same-bank error and oracle headroom | Diagnostic only; not a training regression or causal error label |
| Assignment replay | 568 banks verified; 84/99 recoverable usable-positive banks | Rules out the simple missing-positive explanation | Objective-level explanation remains incomplete |
| Ordering and source-gradient audit | 568 ranks and gradients verified | Tests whether useful candidates rank poorly | Shows a score-level conflict, not parameter dynamics |
| Padding audit | 42 real projection records; small selected-evaluation effect | Tests one representation artifact | Deprioritized as a main bottleneck; not declared harmless in training |
| Margin audit | all 84/99 H velocities negative under independent logits | Qualifies the objective explanation | Does not measure actual parameter updates or shared-head coupling |
| Head source inspection | baseline add_module(shared) versus M95 per-layer head | Identifies a concrete implementation difference | Requires an object- and gradient-level audit before interpretation |

No new terminal experiment appeared in this tick. M184-M188 are legacy structural
controls and are not evidence for a new mechanism.

## 4. Gap Analysis
Q1: What exactly is different between the two scoring heads, and does that
difference create a real cross-layer derivative path?

The next diagnostic must distinguish:

1. source-level class sharing (a class variable exists);
2. instance registration (each decoder layer registers the same object);
3. parameter identity and storage aliasing;
4. checkpoint duplicate-key equality;
5. an actual cross-layer derivative term under a synthetic loss.

Only (1)-(5) can establish the implementation contract. They still do not prove
that the contract caused a real ScanRefer failure. Real head inputs, real losses,
Adam state, dropout, augmentation, and the full decoder graph remain outside the
audit. The current task therefore advances N1/T0 only; it cannot admit a new
mechanism or justify a training run.

Q2: Why not immediately replace the M95 heads with shared heads?

Because the baseline itself already has shared heads and remains below M95 on the
frozen diagnostic sample. Sharing is an existing architecture choice, not a new
contribution. A future mechanism would need a precise error, an explicit
objective, a non-trivial graph change, a verified primary-source distinction,
and a preregistered matched control. None of those are established.

Q3: What would a later core mechanism need?

For any proposed mechanism M, the admission record must specify:

- a concrete failure example and aggregate evidence artifact;
- variables with dimensions, data sources, and test-time availability;
- assumptions and a stepwise derivation from the objective/constraint to the
  forward graph or loss;
- gradients or optimization procedure, degenerate cases, and complexity;
- a verified primary-paper comparison and difference from historical local
  failed variants;
- a matched structural control and a preregistered rejection condition.

## 5. Design Rationale
Q2 is answered by a CPU-only head-ownership and synthetic-coupling audit. The
audit must measure actual object IDs, parameter IDs, storage pointers, duplicate
state keys, checkpoint duplicate values, and the exact synthetic coupling term.
It must also check finite differences and ReLU crossing so the derivative result
is numerically trustworthy.

The formula under test is standard chain rule:

    z_l = h_{theta_l}(x_l), d_l = z_{l,1} - z_{l,0},
    m_l = d_{l,s} - d_{l,h},
    L = sum_l alpha_l L_l(z_l).

For shared parameters theta_l = theta, gradient flow gives:

    theta_dot = -sum_k alpha_k J_k^T g_k,
    dm_l/dt = -alpha_l J_l J_l^T g_l
              -sum_{k != l} alpha_k J_l J_k^T g_k.

For physically independent heads, the cross terms vanish by disjoint parameter
support. The audit tests this implementation fact. It does not turn the chain
rule into a novelty claim.

Q3 outcome: the tick will either establish the exact sharing contract and produce
the first admissible next-step question, or show that the stored checkpoints do
not support the assumed contract. In both cases, no model admission occurs.

## 6. Next Batch
See `pipeline/designs/exp_design_20260911-171500.md`. CPU-only, no new model
package, no training enqueue, no checkpoint mutation, no reserved-scene
inference, and no claim of real-error causality or primary novelty.
