# M95 Coverage Cohort Reconciliation

2026-09-26 14:45 Asia/Shanghai. Read-only analysis, no model execution.

The earlier 32-scene, 123-expression coverage diagnosis reported 85
deployed successes, 33 recoverable errors, and 5 mask-limited cases
(`pipeline/reports/coverage_stage_analysis_20260916.json`). It rejected
the fixed-sampling coverage repair because target loss was 0/117 among
covered targets.

The separate frozen 256-expression exact capture has 200 deployed
successes and 56 failures. Its duplicate-mask audit reports 40 of the
56 failures with at least one target-IoU >0.5 query, leaving 16 with none.
Those 16 are in 16 distinct scenes: 7 selected masks have target IoU 0,
9 have partial target IoU in (0, 0.5], and 5 selected queries are native
matcher-positive. This is a descriptive failure stratum, not 16 newly
proven failures of fixed sampling. The two cohorts, query/mask criteria,
and observed denominators cannot be pooled or used to reverse the
earlier causal rejection.

To reopen coverage as a task mechanism would require a prediction-blind
test that distinguishes candidate generation from existing identity and
mask-quality errors, with a matched intervention on the same native
forward and scene-level negative controls. No such intervention or
native backward/resource/independence receipt exists here. Do not rename
the rejected `same-forward-coverage-diagnosis`, lower the threshold, or
enqueue a sampling/selector variant. Strict 26/65 cross-capture
reproducibility remains failed.

Evidence: `pipeline/reports/m95_duplicate_mask_dominance_20260925-0834.json`
SHA256 `cc65914d4370e8016df4f58521cdfa140f2f4bb9f202765092475e667d608a6f`;
`pipeline/reports/coverage_stage_analysis_20260916.json` was the
earlier cohort source. Numeric counts were independently recalculated
from the frozen duplicate-audit rows in this tick.
