# M95 Exact-Capture Reproducibility Boundary

## Question

Does the failed strict comparison represent a changed referent decision or a
more localized capture drift?

## Method

Compared the immutable 256-row reference identity analysis with the completed
256-row exact-capture postprocess by manifest index and 128-query axis. The
reference analysis SHA256 is
`c7b6e78c64e29144d3abfea5007e5ec0843142b3e7aa6294c600e8eb114d4abb`;
the copied candidate analysis SHA256 is
`9b54eb6f532bec727bad1b7a0701a586487ea636b06ea2c313db1f8482d7232e`.
The source capture is bound to checkpoint
`fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`.

## Result

- The existing strict gate remains **failed**: 28 mismatched rows among 65
  score-matched paired rows, with maximum score delta `5.8651e-5` and maximum
  query-IoU delta `0.0294118`.
- The query-level audit finds scores beyond `1e-6` on 26/256 rows. Only row
  174 exceeds `1e-5`.
- Three query IoUs differ on two expressions: scene0281_00/ann18/query103
  `0.689655 -> 0.666667`; scene0650_00/ann2/query70
  `0.058824 -> 0.029412` and query87 `0.617647 -> 0.588235`.
- No deployed query, selected-query IoU, score-matched pair indices or
  tie-break identity, or query-IoU `>0.5` classification changes.
- Five focused audit tests pass. The audit is CPU-only and read-only.
- A targeted native-artifact comparison on server-6 CPU finds identical target
  unions and physical-instance labels in both rows. Each of the three query
  masks differs by exactly one point. Row 83/query103 adds one non-target
  point (20/29 -> 20/30); row 174/queries70 and 87 each lose one target
  point (2/34 -> 1/34 and 21/34 -> 20/34). The discrepancy therefore
  precedes IoU postprocessing, but its producer-level cause remains unknown.

## Decision Boundary

This narrows the **observed** discrepancy but does not explain its source.
The strict gate must not be relaxed to declare reproducibility. The exact
capture remains useful for bounded, within-capture diagnosis but cannot
establish a population or deployable gain. There is no model mechanism,
native backward, resource comparison, independence receipt, or candidate
admission from this audit. Both queue slots remain empty.

The raw-support comparison is complete. Next executable action, if a new
candidate requires cross-capture reproducibility: inspect the three point
mask logits relative to the frozen threshold and the repeat producer's
determinism settings, then repeat under the original strict contract. Do
not relabel the present failed gate. This measurement work does not reopen
the closed selector, ranking, identity, mask-matching, relation, or duplicate
routes.

## Evidence

- `pipeline/reports/m95_repro_drift_audit_20260925-1013.json`
  SHA256 `177796e6174e07df6b60f90236f3151d685bfb773ca4761c1c365411ffe0520c`
- `scripts/m95_repro_drift_audit_20260925.py`
  SHA256 `499a4c6075b322543dea5692dbee3c9228201fbee47d7a3f9c3b5e5f87e59931`
- `scripts/test_m95_repro_drift_audit_20260925.py`
  SHA256 `56d88b25c2143a88a13b286fb3c79b23c2c5e79aca022d4ede3948f2b3c9e50a`
- `pipeline/reports/m95_exact_capture_reproducibility_20260925-0605.json`
- Local tests: 5/5 passed.
- `pipeline/reports/m95_raw_support_comparison_20260925-1016.json`
  SHA256 `72867e4bf15375733c84ac5b442a0acddf10c4c23f6258e51f432f5056398696`
- `scripts/m95_raw_support_compare_20260925.py`
  SHA256 `6caec50588d218a9a0c72689b8e8b8922db815b4b2356b93b47fe8e444ccc3e4`
