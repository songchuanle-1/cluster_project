================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M17-ORT | State: stopped_unknown (crashed on launch)
================================================================================

## 1. Basic Info
  - ID: M17-ORT
  - Config: configs/Quard/ort/model_base1_quard2_c2f_enc_lite_posA_l1_ort.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-07-22 07:03 / 07:04 (2 attempts) | Finished: crashed immediately
  - Duration: <1s | Epochs: 0/50
  - State: stopped_unknown

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | N/A    | —       |
  | Acc@50   | N/A    | —       |
  | spmIOU   | N/A    | —       |
  (No training iteration completed)

## 3. Convergence Summary
  - Crash before first forward pass completed.
  - Both attempts (07:03, 07:04) created timestamped dirs with only config-copy + 108B log.

## 4. Comparison
  - N/A — no metrics produced.

## 5. Conclusion
  - 结论: [CRASH] — NameError in C2F_ClusterAttn_ORT.forward()
  - 解释: hier_postprocess.py:572 `result[orth_reg_loss]` used undefined variable `orth_reg_loss` as dict key. Fixed to use module-level `_orth_loss_accum` for consistency with dec.py's `get_orth_loss()` collection path.
  - 对后续实验设计的建议: Fix committed (b2db7bd), synced to server-4. Re-queue M17-ORT after next tick confirms fix works. Mechanism remains untested.

## 6. Crash Info
  - Error type: NameError (variable not defined)
  - Error message excerpt: `NameError: name 'orth_reg_loss' is not defined` (inferred from code analysis)
  - Auto-fix attempt: Y — 1 retry, result: fixed (code patched, queued for retry)
================================================================================
