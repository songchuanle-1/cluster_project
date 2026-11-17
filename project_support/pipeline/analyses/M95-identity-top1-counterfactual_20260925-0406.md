# M95 Identity Top-1 Counterfactual

## Question

Does the support-excluded identity margin retain its pair-level advantage when
it must choose one query per expression from the same candidate universe as
native scores?

## Method

- Source: frozen 256-expression M95 identity capture
  `f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025`.
- For every query with a finite support-floor-3 identity margin, compare
  native-score top-1, identity-margin top-1, and oracle-IoU top-1 on the same
  expression-local candidate universe.
- Report expression-level paired deltas with scene-cluster bootstrap intervals,
  leave-one-scene-out sensitivity, success above `0.5` IoU, and a
  within-expression identity-margin permutation null.
- This is oracle diagnostic evidence. It does not establish a deployable
  selector, native backward, resources, novelty, or admission.

## Results

The audit evaluated `9,362` identity-eligible queries from `16,384` attempted
queries across `121` expressions and `121` scenes. Identity changed the
selected query in `119/121` expressions.

| Selector on the common eligible universe | IoU > 0.5 |
|---|---:|
| Native score | 20.66% |
| Support-excluded identity margin | 9.92% |
| Oracle query | upper bound |

Identity-minus-score mean IoU was `+0.00725` with scene-bootstrap 95% CI
`[-0.05630,+0.07158]`. It improved `70` expressions, worsened `36`, and tied
`15`. The oracle-minus-score headroom was `+0.36724` with 95% CI
`[+0.31982,+0.41551]`.

Against the preregistered within-expression permutation null, the observed
mean was `+0.00725`, while the null mean was `-0.07102` with 95% interval
`[-0.10358,-0.03695]`. The association is non-random, but its direction and
magnitude do not support identity margin as a top-1 selector.

## Interpretation

The earlier pair-level result shows that identity margins can order some
score-matched target/peer disagreements. This expression-level test shows that
the relation is not compositional: choosing the maximum identity margin over
the broader eligible query set misses acceptable masks much more often than
native score selection. The evidence rejects identity-margin top-1 selection;
it does not reject every possible identity representation or supervision
mechanism.

## Decision

- Keep `referent-supervision-axis`, `referent-discrimination`, and
  `instance-identity-representation` at validation.
- Do not create an identity-margin selector or any renamed selector variant.
- Continue exact native match-cause capture as the remaining attribution step
  for score, supervision, geometry, and mask-component causes.

## Evidence

- `pipeline/reports/m95_identity_top1_counterfactual_20260925-0406.json`
  `sha256=82fc1cc2485ee0f4a4d7b604927989efcfaffd2af4a8d7be69be3b962ffc122e`
- `scripts/m95_identity_top1_counterfactual_20260925.py`
  `sha256=cb7b8851361f7655a65c5ec17a5dbb0a0fb0d4bfc3284c2df916b0b2c2c99727`
- `scripts/test_m95_identity_top1_counterfactual_20260925.py`
  `sha256=4a3cac304771556c00922485bccca2e5f0b72be290a936c37ad1439107dce041`
- `pipeline/decisions/20260925-040536_route_change.md`
  `sha256=a0b4f12d699bf668ef453c9463579f2f409b23d474442ea40497ec7599e01c31`
