# M95 Full-Order First-Stage Completion

2026-09-26 15:31 Asia/Shanghai. Stable diagnostic ID
`m95-repro-drift-boundary`. The guarded server-6 GPU7 run completed
row83 at original-order step3137; remote `status` is complete and the
progress-stream output SHA256 equals the retrieved result SHA256
`bef5bea0689df9dd8e2985a5b344e13b6fb400fe2c6fa182e4083e856679024b`.
The frozen config, checkpoint, manifest, saved batch, and earlier
full-order trace identities are recorded in the result.

The original-order pass and saved-batch replay in the *same process*
have equal SHA256 at sparse input, first sparse output and final sparse
output, including their index tensors. All six comparisons have zero
changed elements. Their `p2v_map` and `superpoints` hashes match. Both
select query2 at target IoU 0. The point169 logit is about 4.03e-6
versus 9.26e-6; it does not change that selected outcome.

This resolves the within-process first-stage question for this frozen
item, but not the historical capture discrepancy: historical upstream
feature hashes are unavailable and the separate strict comparator still
fails 26/65 paired rows. A numerically fragile threshold is a provenance
finding, not a task-specific structural mechanism. No matched task
control, native backward, resource or independent variant receipt exists.
No training admission or queue change is justified.

Evidence: `pipeline/reports/m95_first_stage_result_20260926-1521.json`.
Do not restart the completed probe to fill a training slot.
