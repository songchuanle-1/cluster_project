================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M28-ORT-W1 | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M28-ORT-W1
  - Config: configs/Quard/ort_w1/model_base1_quard2_c2f_enc_lite_posA_l1_ort_w1.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-07-28 05:03 | Finished: ~2026-07-28 07:03 | Duration: ~2h
  - State: stopped_unknown (process disappeared during epoch 4/50 training)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.3916 | 3       |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (only 3 epochs completed — metrics too early to be meaningful)

## 3. Convergence Summary
  - Best first reached at: epoch 3 (0.3916)
  - Subsequent no_improve epochs: N/A (only 3 epochs)
  - Final epoch best: mIoU=0.3916
  - 收敛形态: 仅 3 epochs, 初期快速上升中 (0.3333→0.3853→0.3916), 远未收敛即被中断

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = -0.0978 (大幅落后, 但仅3 epochs不可比)
  - vs champion (posA_l1=0.5012): γ = -0.1096
  - vs M17-ORT (orth_weight=0.01, Best=0.5005): γ = -0.1089
  - vs M27-ORT-W5 (orth_weight=0.05, Best=0.4959): γ = -0.1043
  - 注: 仅 3 epochs 数据，以上对比无统计意义

## 5. Conclusion
  - 结论: [无效数据] — 仅 3 epochs 即被中断，数据不足以判断 orth_weight=0.001 的效果
  - 解释: 实验在 ep4 训练中进程消失。与 M27(ort_w5) 同时段被中断，可能是系统级原因(server-4 同时段两个进程均消失)。
  - 对后续实验设计的建议: 不基于此数据做决策。orth_weight 最优值已由 M17(0.01=0.5005) 确认，无需重跑 M28。

## 6. Crash Info (if crashed)
  - Error type: silent process death (stopped_unknown)
  - Error message excerpt: N/A — process disappeared during epoch 4 training, no error logged
  - Auto-fix attempt: N (experiment terminated too early; orth weight sweep already complete with M17/M27)
================================================================================
