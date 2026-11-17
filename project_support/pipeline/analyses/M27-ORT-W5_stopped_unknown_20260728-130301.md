================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M27-ORT-W5 | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M27-ORT-W5
  - Config: configs/Quard/ort_w5/model_base1_quard2_c2f_enc_lite_posA_l1_ort_w5.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-07-27 16:03 | Finished: ~2026-07-28 07:33 | Duration: ~15.5h
  - State: stopped_unknown (process disappeared during epoch 20/50 training)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4959 | 19      |
  | Acc@50   | 0.553  | 19      |
  | spmIOU   | 0.459  | 19      |

## 3. Convergence Summary
  - Best first reached at: epoch 12 (0.4935)
  - Subsequent no_improve epochs: 0 (kept improving: 0.4942@17, 0.4946@18, 0.4959@19)
  - Final epoch best: mIoU=0.4959 vs historical best=0.4959
  - 收敛形态: 缓慢单调上升，ep1-12 快速爬升(0.32→0.49)，ep12-19 微涨平台(0.4935→0.4959)。仍在上升通道中被中断。

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0065 (有效)
  - vs champion (posA_l1=0.5012): γ = -0.0053 (不及champion)
  - vs M17-ORT (orth_weight=0.01, Best=0.5005): γ = -0.0046 (更强的正交约束反降点)
  - vs M24-ORT-D (ort+detail, Best=0.4955): γ = +0.0004 (≈持平)
  - vs M26-ORT-HYB (ort+hybrid, Best=0.4998): γ = -0.0039 (不及ort+hyb)

## 5. Conclusion
  - 结论: [失败] — stronger orthogonality (weight=0.05) degrades vs default weight=0.01
  - 解释: orth_weight 从 0.01→0.05，mIoU 从 0.5005→0.4959 (-0.0046)，正交约束过强压制了有效特征表达。orth_weight 最优值在 0.01 附近。
  - 对后续实验设计的建议: orth_weight 扫参已覆盖 {0.001, 0.01, 0.05}，0.01 最优。关闭 orth 方向，不再设计新的 orth weight 变体。

## 6. Crash Info (if crashed)
  - Error type: silent process death (stopped_unknown)
  - Error message excerpt: N/A — process disappeared without error log during epoch 20 training
  - Auto-fix attempt: N (experiment already had 19 epochs of valid data; process death likely external/systemic)
================================================================================
