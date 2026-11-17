# M95 Identity Component Decomposition

## Question

Is the support-excluded pair-level identity advantage explained by target
attraction, peer rejection, or their combination?

## Method

- Source: frozen 256-expression M95 identity capture
  `f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025`.
- Final-stage features, support floor 3, score-match tolerance 0.1, and the
  same `1,833` target-positive/peer score-matched pairs as the corrected
  support-sensitivity audit.
- Compare three fixed selectors on identical pairs: higher target similarity,
  lower peer similarity, and higher full identity margin
  (`target similarity - peer similarity`).
- Decompose each identity-score disagreement into the change in target
  similarity and the change in peer similarity for the identity-selected query
  relative to the score-selected query.
- This is oracle diagnostic evidence. It does not establish a deployable
  selector, native backward, resources, novelty, or admission.

## Results

| Pair-level selector | Accuracy | Delta vs native score |
|---|---:|---:|
| Target similarity alone | 100.00% | +23.62pp |
| Low peer similarity alone | 77.20% | +0.82pp |
| Full identity margin | 89.53% | +13.15pp |

Target similarity alone disagreed with native score on `433` pairs and chose
the higher-IoU query on all `433`. Its target-query clustered delta was
`+23.62pp`, 95% CI `[+18.93,+28.25]pp`.

Peer rejection alone had `529` score disagreements but only `272` wins and
`257` losses. Its target-query clustered delta was `+0.82pp`, 95% CI
`[-7.16,+8.87]pp`, so peer rejection alone is not evidenced as better than
native score.

Among the `389` non-tied identity-score disagreements:

- `272` had both higher target similarity and lower peer similarity; all
  `272` selected the higher-IoU query.
- `43` had only higher target similarity; all `43` selected the higher-IoU
  query.
- `74` had lower peer similarity but lower target similarity; all `74`
  selected the lower-IoU query.

Across these disagreements, the identity-selected query averaged `+0.02531`
target-similarity delta (target-query bootstrap 95% CI
`[+0.01297,+0.03991]`) and `-0.03701` peer-similarity delta (95% CI
`[-0.05118,-0.02562]`). The losses are exactly the peer-rejection-only
subpopulation where target similarity moves in the wrong direction.

## Interpretation

The current pair-level identity advantage is target attraction. Adding peer
rejection to target similarity is not supported: the full margin is worse
than target similarity alone, and every observed loss occurs when peer
rejection overrides adverse target evidence. The perfect target-similarity
pair ordering uses oracle instance prototypes and is not a deployable result,
but it closes peer-specific identity discrimination as the useful component
of this diagnostic.

The result narrows the open supervision axis toward target-positive binding,
not distractor rejection. Exact native match-cause capture remains required
before deciding whether score, supervision, geometry, or mask components are
the actionable cause.

## Decision

- Reject `referent-discrimination` as a peer-rejection or identity-margin
  hypothesis on concrete component evidence.
- Reject standalone `instance-identity-representation` as noncompositional:
  target similarity alone dominates the full margin and identity-margin top-1
  already failed.
- Keep only `referent-supervision-axis` in validation. Resume the exact native
  postprocess when the running capture finishes; do not launch a duplicate.
- Do not create a selector or peer-rejection variant from this oracle result.

## Evidence

- `pipeline/reports/m95_identity_component_decomposition_20260925-0520.json`
  `sha256=b7ce694765693e91e15d47e38f351ad75b5cb76c865266d8f728ec7195392552`
- `scripts/m95_identity_component_decomposition_20260925.py`
  `sha256=a4aab8930d42aff2d0c7052a3028261ed39a7166727ac795fd0ff319f38a4a6c`
- `scripts/test_m95_identity_component_decomposition_20260925.py`
  `sha256=eb78c665da96f60726445e00276fdb4ff58d3230a96f35dc328e15f4528e5bac`
