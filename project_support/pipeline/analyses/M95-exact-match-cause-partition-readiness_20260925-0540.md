# M95 Exact Match-Cause Partition Readiness

## Goal

The active `referent-supervision-axis` validation needs to distinguish why
target-positive query membership has oracle value. The exact full-scan capture
stores native `nearest_gt` and `instance_member` causes, but the existing
postprocess does not partition all 256 expressions by those causes.

## Implemented Diagnostic

`scripts/m95_exact_match_cause_partition_20260925.py` will validate the exact
capture contract and classify every query as:

- nearest to the target object;
- an instance member of the target object;
- positive only through another object; or
- negative.

For each expression it compares the deployed query with oracle top-score
queries inside the full native-positive set, target-positive set,
target-nearest set, and target-member set. It reports paired scene-bootstrap
intervals over IoU and IoU>0.5 success while preserving the exact query choice.

The goal is diagnostic attribution only: whether target-specific oracle value
is carried by native nearest anchors, native instance membership, or their
union. It does not create a selector, loss, model variant, or admission claim.

## Verification

- Local focused tests: `8/8` passed.
- Server-6 CPU focused tests: `8/8` passed.
- Python compilation passed locally and in the remote diagnostic bundle.
- Analyzer SHA256:
  `6f329451624a65d2805b3f108f8b78a3cfe8a29209918535ae6702318e0b23b7`.
- Test SHA256:
  `d1f29c0b7b4e76c3878fe222de2b3016ce6837cf69d93412c8dd4b75a865aca0`.

## Native Status

Exact capture PID `3140840` remained alive on server-6 GPU7 and was observed
at step `4288/4663`, with `234` expressions and no `capture.json`. No duplicate
capture was launched.

## Decision Boundary

No native cause-partition result or admission exists yet. The analyzer must run
only after the fail-closed postprocess validates the complete exact capture.
