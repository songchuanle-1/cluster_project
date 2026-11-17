# M95 Partition Drift Localization

## Question

Does the row-174 final-stage divergence coincide with a changed hierarchical
partition in two immutable M95 captures?

## Method

Compared SHA256-verified frozen captures on server-6 CPU, validating each
hierarchy row against its recorded partition digest and the native input
fingerprint. Localized per-point final-feature drift and compared level-wise
cluster assignments. Four focused tests passed. No model forward or GPU
diagnostic ran.

## Result

- Both rows retain the same native input fingerprint across captures, but
  their hierarchy hashes differ. Row 83 has zero changed assignments at all
  three levels, with final feature maximum delta under 4e-6.
- Row 174 has exactly one changed level-0 assignment among 860 points:
  point 344. Levels 1 and 2 have zero changed assignments. Its hierarchy
  positions and child maps also differ, but this audit does not establish
  whether those differences are numerically material or causal.
- The same point 344 is a target point, loses membership in query 87's
  thresholded mask and has the largest final-feature delta, 0.170507.
  Fifteen points have final-feature max delta >1e-3; point 344 accounts
  for 85.6% of total squared final-feature drift. Its fused input max
  delta is only 1.19e-6.
- The source point coordinates and the two nearest-center distances were
  not saved in the frozen hierarchy row. A distance-margin calculation
  cannot be made from that schema; an attempted extension failed closed
  and was removed.

## Disposition

The assignment/feature coincidence is a reproducibility lead, not proof that
the partition caused the output change. The original strict 65-pair comparison
still fails at 28 mismatches; do not relax it. When server-6 GPU7 is safely
free, run the same checkpoint/manifest/producer family with explicit
partition input coordinate, nearest two distances, assignment, cluster
readback and decoder-query boundaries for rows 83 and 174; verify hashes
and repeat the unchanged strict gate. GPU7 remained at 100% utilization
with foreign PID 3694608 using 41996 MiB, so no native repeat or model
training launched. This audit provides no model mechanism, native backward,
resource gate, novelty, or admission.

## Evidence

- `pipeline/reports/m95_final_stage_drift_20260925-1115.json`
  SHA256 `53af5fa3db3c97572f34f377e1889c46ccd3458ec7b677c047bda5e47352c728`
- `pipeline/reports/m95_partition_drift_20260925-1115.json`
  SHA256 `ad48b55e815ed1ea42e901356bb99fc33a81e7e181aded099b569ba8bf513753`
- `pipeline/reports/m95_partition_repeat_block_20260925-1118.json`
- `scripts/m95_final_stage_drift_20260925.py` and
  `scripts/m95_partition_drift_20260925.py` (read-only analyzers).
