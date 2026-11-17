# M95 Identity Support Sensitivity

## Question

Does query-support exclusion eliminate the target-versus-peer identity advantage
after correction for pair-enumeration order?

## Method

- Source: frozen 256-expression M95 identity capture
  `f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025`.
- Control: subtract each candidate query's labeled support from target and peer
  prototypes before cosine classification.
- Fixed support floors: 1, 2, and 3. All floors are reported; no floor is used
  for selection.
- Full matching: every score-matched target-positive/peer pair in the common
  population.
- Nearest-peer matching: one closest-score peer per target-positive query.
- Corrected pair construction stores all query rows before pairing. The earlier
  `515`-pair result only matched peers to target queries already encountered in
  the loop and is order-biased.

## Final-Stage Results

| Support floor | Full pairs | Identity minus score | Scene-bootstrap 95% CI |
|---:|---:|---:|---:|
| 1 | 1833 | +15.44pp | [+10.67,+38.61] |
| 2 | 1833 | +13.15pp | [+9.17,+38.00] |
| 3 | 1833 | +13.15pp | [+9.17,+38.00] |

The common population contains 6,397 queries. The nearest-peer control contains
134 common pairs:

| Support floor | Nearest peers | Identity minus score | Scene-bootstrap 95% CI |
|---:|---:|---:|---:|
| 1 | 134 | +32.09pp | [+18.76,+56.47] |
| 2 | 134 | +30.61pp | [+23.01,+57.86] |
| 3 | 134 | +31.85pp | [+17.12,+53.92] |

## Stage Locality

At support floor 3, full-pair identity-minus-score is negative for raw/projected
2D features (`-48.72pp`/`-60.17pp`), positive for raw/projected 3D features
(`+12.88pp` each), `+7.15pp` for the fused stage, and `+13.15pp` for the final
stage. The diagnostic therefore localizes the identity-over-score relation to
3D and later representations rather than supporting a general representation
deficiency claim.

## Decision

- Supersede the `20260925-0200` claim that support-excluded identity superiority
  is not established.
- Keep all three due IDs at validation until the exact native match-cause
  capture finishes and the fail-closed postprocess chain distinguishes score,
  supervision, geometry, and mask-component causes.
- Treat this as oracle diagnostic evidence only. It does not establish
  deployability, native backward, resource compliance, novelty, or admission.

## Evidence

- `pipeline/reports/m95_identity_support_sensitivity_20260925-0248.json`
  `sha256=baaba41beb319329e4262456b636344dd49f12bfa37a6154f1683fd12f549904`
- `scripts/m95_identity_support_sensitivity_20260925.py`
  `sha256=5d3f4da568f5d534b37e752a46db3925522d6e36f9f44afd4e8d43030ab99cf0`
- `scripts/test_m95_identity_support_sensitivity_20260925.py`
  `sha256=9c1f7cfc4c70afcd8155dee1b2ddb934dea3d72a99c1287d201210264364c48a`
- `pipeline/decisions/20260925-022629_route_change.md`
  `sha256=c2a492afb3c079bc6d7a19ff74d7dc2674ddb6cb38f7fff6f5d415448b53cca8`
