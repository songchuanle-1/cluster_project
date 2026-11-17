# M95 Target-Positive Cardinality Control

## Question

Does the native target-positive selection advantage survive controls that
preserve positive cardinality and score ranking?

## Method

- Source: the frozen 256-expression M95 identity-control analysis
  `c7b6e78c64e29144d3abfea5007e5ec0843142b3e7aa6294c600e8eb114d4abb`.
- For every expression, select the highest frozen-score query from the native
  positive set.
- Compare against the highest-score query from the same-cardinality top-score
  set, and against `2,000` uniform random subsets of exactly the same
  cardinality. Select the highest-score query within each sampled subset.
- Report expression and scene-balanced paired IoU, success deltas, and a
  scene-cluster bootstrap (`10,000` draws, seed `1999`).
- This is a CPU-only placebo/control diagnosis. It does not establish a
  deployable selector, native backward, resources, novelty, or admission.

## Results

The audit covers `256` expressions and `220` scenes. Native-positive
cardinality ranges from `1` to `51`, with mean `7.02`.

| Selector | Success | Mean IoU |
|---|---:|---:|
| Native-positive top-score | `88.28%` | `0.7784` |
| Same-cardinality top-score | `78.13%` | `0.6818` |
| Cardinality-matched random mean | `51.18%` | `0.4561` |

Native-positive selection exceeds the random control by `+0.32082`
scene-balanced IoU, with 95% CI `[+0.28725,+0.35430]`. Its success rate
exceeds the random mean by `+0.37042`, 95% CI `[+0.32846,+0.41324]`.

The native-positive top-score selector changes the choice on `49` expressions
relative to the same-cardinality top-score selector. It improves
scene-balanced IoU over that selector by `+0.10229`, 95% CI
`[+0.06870,+0.13806]`.

The mean positive-set IoU quantile against the random subsets is `0.7451`;
`14.45%` of expressions place at or below the random median. The random
control is therefore materially weaker despite exactly matching native
positive-set cardinality.

## Interpretation

The selection advantage is not explained merely by restricting the candidate
set to a smaller cardinality. It also is not reproduced by taking the highest
native scores with the same cardinality. Native-positive membership identifies
different queries on `49` expressions and those identities carry substantial
oracle value.

This strengthens target-positive binding as the remaining open supervision
axis while preserving the earlier conclusion that pair-level identity and
oracle selection are not deployable mechanisms. Exact full-stream native
match-cause capture is still required to determine why the native positive
set differs from score rank and whether score, geometry, mask components, or
query support causes the difference.

## Decision

- Keep `referent-supervision-axis` in validation.
- Do not reopen selector, identity-margin, listwise-ranking, or peer-rejection
  routes from this oracle result.
- Continue monitoring exact capture PID `3140840`; run the fail-closed
  postprocess only when `capture.json` exists with complete frozen bindings.

## Evidence

- `pipeline/reports/m95_target_positive_cardinality_control_20260925-0531.json`
  `sha256=6eb806527ce882074aa9a645233f28430d31ce6763b0db1f1d44a6f27c7cc2f0`
- `scripts/m95_target_positive_cardinality_control_20260925.py`
  `sha256=11780eccf2ad834db4918d5e75f7cb2bf53343c48b5cb438ee2864ee9635dfdb`
- `scripts/test_m95_target_positive_cardinality_control_20260925.py`
  `sha256=8aafc80f5fdae3d399a00efc435396197c9323571473823de9af3270044ea00f`
- `pipeline/decisions/20260925-052952_route_change.md`
  `sha256=0ce5f3050e68aefa1e712e1769e583afa6042f23e93c77a84c21531d464b8d33`
