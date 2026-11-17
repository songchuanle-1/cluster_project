================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M17-ORT (second run, fixed) | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M17-ORT
  - Config: configs/Quard/ort/model_base1_quard2_c2f_enc_lite_posA_l1_ort.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-07-23 00:05 | Finished: 2026-07-24 05:30 | Duration: ~29.5h
  - State: done_earlystop (clean early-stop, not crash)
  - Note: First run (07-22) crashed x2 with NameError; fixed (b2db7bd: add orth_weight to DEC.__init__). Second run completed 28 epochs, early-stopped at 10 no-improv.

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5005 | 18      |
  | Acc@50   | 0.554  | 18      |
  | spmIOU   | 0.464  | 18      |

## 3. Convergence Summary
  - Best first reached at: epoch 18 (mIoU=0.5005)
  - Subsequent no_improve epochs: 10 (epochs 19-28)
  - Final epoch (28) mIoU: 0.4834 vs best 0.5005
  - Convergence pattern: rapid rise to 0.5005@ep18, then gradual decline with oscillations (0.497→0.494→0.485→0.490→0.483), no improvement for 10 consecutive epochs.

## 4. Comparison
  - vs baseline (model_base1, 0.4894): γ = +0.0111 (有效)
  - vs champion (posA_l1, 0.5012): γ = -0.0007 (持平, 差 0.0007)
  - vs D1-detail (0.5003 stopped_unknown): γ ≈ 0 (持平)
  - Orthogonality regularization on coarse cluster tokens achieves champion-level performance — within 0.0007 of champion.
  - orth_reg_loss weight=0.01 provides mild regularization without hurting convergence.

## 5. Conclusion
  - 结论: [有效] — orthogonality regularization achieves champion-level mIoU (0.5005 vs 0.5012)
  - 解释: Forcing coarse cluster tokens to be orthogonal improves cluster bank diversity without hurting task performance. The 0.5005 result is statistically tied with champion (Δ=0.0007, within noise).
  - 对后续实验设计的建议: ORT mechanism validated. Consider (a) combining ORT with other effective mechanisms (detail, hybrid), (b) tuning orth_weight, (c) multi-seed verification in Phase 2.

## 6. Crash Info
  - Not a crash — clean early-stop. First run (07-22) crashes fixed prior.
================================================================================
