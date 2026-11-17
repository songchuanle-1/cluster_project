================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M65-HCG | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M65-HCG
  - Config: configs/Quard/hcg/model_base1_quard2_c2f_enc_lite_posA_l1_hcg.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-07 07:03 | Finished: 2026-08-08 03:59 | Duration: ~21h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5002 | 21      |
  | Acc@50   | 0.554  | 21      |
  | spmIOU   | 0.462  | 21      |

## 3. Convergence Summary
  - Best first reached at: epoch 21 (mIoU 0.500)
  - Subsequent no_improve epochs: 10 (early-stopped at epoch 31)
  - Convergence form: 快速上升 (ep1-21 0.343→0.500) 后 10 epoch 平台期 0.489-0.497 震荡未再破 best
  - 序列末5: 0.491, 0.489, 0.491, 0.489, 0.489 — 持续下行定格在 best 下方

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0108 (有效)
  - vs current champion (posA_l1/DRP=0.5012): γ = -0.0010 (持平, 距 champion 仅 0.0010)
  - vs detail (D1=0.5003): γ = -0.0001 (持平, HCG 正确交付与 detail 残差 message 同为 0.500 水平)

## 5. Conclusion
  - 结论: [持平]
  - 解释: HCG (逐级组合点→簇映射, 修复粗尺度 readback 长度错配) 达到 0.5002,
    与 champion 0.5012 / detail 0.5003 处于同一水平 — 正确多尺度交付把"残缺交付"的
    隐性损失补上了, 但本身不带来新的上限, 只是消除短板。γ=+0.0108 确认 HCG 是
    必要修复, 但不是突破 0.51 的增量来源。
  - 对后续实验设计的建议: HCG 作为"交付正确性"基线已经确立 (0.5002), 后续组合实验
    (M66-DET-HCG, M72-CCP-HCG, M74-CCP-HCG-DET) 应把 HCG 视为正确交付标准组件,
    增量看另一轴 (detail/CCP)。HCG 单独不再重复, 组合跑 M66 中。

================================================================================
