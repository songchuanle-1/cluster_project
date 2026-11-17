================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M62-ORTG | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M62-ORTG
  - Config: configs/Quard/ortg/model_base1_quard2_c2f_enc_lite_posA_l1_ortg.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-06 07:03:21 | Resumed: 2026-08-06 20:09 | Finished: 2026-08-06 23:54
  - Duration: ~15h active (07:03→17:59 首段 + 20:09→23:54 resume 段; 中间 2h 为外部 fineweb-edu 资源冲突停滞)
  - State: done_earlystop (Early stopping at epoch 23: no improvement for 10 epochs, best=0.4979)
  - Note: M62 = cluster_mode drp_ort (DRP champion 机制 + 真梯度 ORT). 2026-08-06 20:09 从 last.pth resume
    (start_epoch:18, best_miou 0.4979, epochs_no_improve:4), 上 tick 已处置外部资源冲突并验证恢复.

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4979 | 18      |
  | Acc@50   | 0.551  | 18      |
  | spmIOU   | 0.462  | 18      |

## 3. Convergence Summary
  - Best first reached at: epoch 18 (mIoU=0.4979, 首段 07:03 运行达成)
  - Resume 后 6 个 epoch (18-23) 验证: 0.491 / 0.495 / 0.486 / 0.493 / 0.491 / 0.485 — 均未刷新 best
  - no_impr 计数: resume 携带 4 + resume 后 6 = 10 → epoch 23 触发 early stop
  - 收敛形态: 首段上升至 0.4979@ep18 后进入平台/回落 (0.495→0.486→0.493→0.491→0.485), 无后续刷新

## 4. Comparison
  - vs baseline (model_base1, 0.4894): γ = +0.0085 (有效, 高于 baseline)
  - vs champion (posA_l1/DRP, 0.5012): γ = -0.0033 (失败)
  - vs M17-ORT (0.5005, 断流梯度版 ORT 单独): γ = -0.0026 (低于单独 ORT)
  - vs M32-DRP (0.5012, DRP 单独): γ = -0.0033 (低于单独 DRP)
  - 结论链条: DRP+真梯度ORT 组合 (0.4979) < M17-ORT 断流版 (0.5005) ≈ champion DRP (0.5012)
    → 修复 orth 梯度断流后, ORT 惩罚真正回传反噬任务损失; 断流版的弱正则反而无碍.

## 5. Conclusion
  - 结论: [失败] — 真梯度 ORT 与 DRP 组合未达 champion, 且低于单独 ORT / 单独 DRP
  - 解释: M17-ORT(断流梯度 0.5005)的收益来自 orth 弱正则而非强约束; M62-ORTG 修复梯度后
    orth_loss 强回传, 与任务 loss 竞争, token 多样性提升不足以抵消定位精度损失.
    DRP + ORT 无协同 (2×2 组合 -0.0033 双输).
  - 对后续实验设计的建议: (1) ORT 路线以 M17-ORT 断流版 0.5005 为准, 不继续修梯度;
    (2) DRP 仍是 champion 机制 (0.5012), 后续组合应围绕 DRP × 其他 message 构造轴 (M64-SSP/M65-HCG 已在队);
    (3) 队列中 M58-DET-DRP/M66-DET-HCG 等 detail×DRP 组合继续观察, 不与 ORT 再组合.
