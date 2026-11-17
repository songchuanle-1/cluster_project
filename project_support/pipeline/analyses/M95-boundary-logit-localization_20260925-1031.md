# M95 Boundary-Logit Localization

## Question

Are the three exact-capture mask changes simply zero-threshold numerical flips,
or does one row diverge earlier in the native forward path?

## Method

Compared only rows 83 and 174 of the two immutable, SHA256-verified native
captures. Each artifact hash was verified before loading. Checked that the
stored boolean mask equals `query_mask_logits > 0` for each implicated query,
then compared saved raw/projected/fused/final feature stages. This is a
read-only CPU audit on authorized server-6; three focused tests passed there.
Local Python lacks torch and did not run those tests.

## Result

- Row 83/query103/point169 changes `-2.3711e-7 -> +1.0489e-6` at the
  threshold. Its maximum final feature delta is `3.8147e-6`; raw 2D is
  identical. One non-target point enters the predicted mask.
- Row 174/query70/point364 changes `+0.031101 -> -0.017660` and
  query87/point344 changes `+0.213800 -> -0.349709`. These are target-point
  losses, not merely near-zero rounding of a stable logit.
- Row 174's maximum raw 3D delta is `4.8876e-6`, raw/projected 2D is
  identical, and maximum fused delta is `6.0201e-6`. Its final-stage delta
  reaches `0.170507`; mean absolute final delta is `9.4741e-5`.
- Neither capture saves `identity_query.query_states`, so the precise
  decoder-to-head localization is unavailable. The producer seeds at
  initialization and before each forward, uses batch size 2 and zero data
  workers, but the inspected source does not explicitly enable deterministic
  CUDA algorithms. That observation is not proof of the cause.
- The existing 28/65 strict paired-row mismatches, max score delta
  `5.8651e-5` and max IoU delta `0.0294118` remain a **failed** strict gate.
  The earlier query audit found no deployed-selection or selected-IoU flip.

## Disposition

This is a measurement/provenance audit, not a new model mechanism or a
deployable result. No diagnosis/control/native-backward/resource/independence
chain for a training candidate is complete; neither slot is admitted. The
row-174 divergence warrants a same-producer, same-checkpoint native repeat
with saved decoder/query-state boundaries and the original strict comparator,
not a post-hoc tolerance change. First verify GPU7 occupancy and memory; the
observed foreign process PID 3694608 consumed 41996 MiB at 100% utilization.
Do not evict it or use any non-whitelisted GPU. Retry only when GPU7 is
available with safe headroom, then isolate the divergent operation and repeat
the original strict gate. No capture or training run was launched this tick.

## Evidence

- `pipeline/reports/m95_boundary_logit_audit_20260925-1027.json`
  SHA256 `19f0ba3ba53083e9438cca038914027110a43f426a786e8f455d268282e286f0`
- `scripts/m95_boundary_logit_audit_20260925.py`
  SHA256 `10c5a805f860a4837f6e92ac2560ec11327038030b143568016863e948ef933a`
- `scripts/test_m95_boundary_logit_audit_20260925.py`
  SHA256 `edea7c1f1b78d8ca974d10fc3fb1bf6db287165a637ff8004a2cbf188dcafcff`
- `pipeline/reports/m95_exact_capture_reproducibility_20260925-0605.json`
  and `pipeline/reports/m95_raw_support_comparison_20260925-1016.json`.
