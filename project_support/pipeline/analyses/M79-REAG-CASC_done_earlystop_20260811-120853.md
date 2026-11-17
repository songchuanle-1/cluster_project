================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M79-REAG-CASC | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M79-REAG-CASC
  - Config: configs/Quard/reag_casc/model_base1_quard2_c2f_enc_lite_posA_l1_reag_casc.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-10T15:46:13 | Finished: 2026-08-11T04:07:00 | Duration: ~12h21m
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4919 | 18      |
  | Acc@50   | 0.543  | 18      |
  | spmIOU   | 0.456  | 18      |

## 3. Convergence Summary
  - Best first reached at: epoch 18
  - Subsequent no_improve epochs: 10 (early-stopped at ep28)
  - Final epoch best: mIoU=0.4919 vs historical best=0.4919
  - 收敛形态: ep18 达峰 0.4919 后 10 epoch 未刷新 (末值 0.483), 自然早停

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0025 (微有效)
  - vs current champion (model_base1_quard2_c2f_enc_lite_posA_l1 0.5012): γ = -0.0093
  - vs M70-REAGG (0.4983): γ = -0.0064 (修复 lvl>0 缺陷后反降, 单一变量对照失败)
  - vs M78-REAGG-HCG (0.5008): γ = -0.0089
  - 前置: M79 = 修复 M70-REAGG 的 _reaggregate lvl>0 缺陷, 单一变量对照; 但 M70 原实现 0.4983 > M79 修复版 0.4919

## 5. Conclusion
  - 结论: [失败]
  - 解释: "级联正确重聚合"(修复 M70 lvl>0 缺陷) 作为单一变量不仅未破顶, 反较 M70 原缺陷版下降 0.0064 — REAGG 轴的正确实现无独立增益, 修复链单独无效
  - 对后续实验设计的建议: 修复链的增益只能寄望 M80 (REAGG+级联×HCG) 与 HCG 组合; 若 M80 也不破顶则 REAGG 轴整体放弃, 转回 token 质量轴 (CTF) / query 调制 (QMOD) / 多层注入 (MLAY)

## 6. Crash Info (if crashed)
  - 无 crash; 正常 early-stop (log: Early stopping at epoch 28, best=0.4919)
================================================================================
