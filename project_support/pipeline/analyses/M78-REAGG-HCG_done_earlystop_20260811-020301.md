================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M78-REAGG-HCG | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M78-REAGG-HCG
  - Config: configs/Quard/reag_hcg/model_base1_quard2_c2f_enc_lite_posA_l1_reag_hcg.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-10T10:00:17 | Finished: 2026-08-11T01:22:00 | Duration: ~15h22m
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5008 | 14      |
  | Acc@50   | 0.554  | 14      |
  | spmIOU   | 0.465  | 14      |

## 3. Convergence Summary
  - Best first reached at: epoch 14
  - Subsequent no_improve epochs: 10 (early-stopped at ep24)
  - Final epoch best: mIoU=0.5008 vs historical best=0.5008
  - 收敛形态: 快速上升至 ep14 达峰 0.5008 后平台震荡 10 epoch (末值 0.493), 触发早停

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0114 (有效)
  - vs current champion (model_base1_quard2_c2f_enc_lite_posA_l1 0.5012): γ = -0.0004
  - vs M65-HCG alone (0.5002): γ = +0.0006
  - vs M70-REAGG alone (0.4983): γ = +0.0025
  - 前置: M78 = reag(迭代+重新聚合) × HCG(正确多尺度交付), 对照 M72-CCP-HCG (0.4950) / M74 三维满格 (0.4948)

## 5. Conclusion
  - 结论: [有效但未破顶]
  - 解释: REAGG × HCG 0.5008 是 HCG 轴上的最佳组合 (超过 HCG alone 0.5002), 距 champion 0.5012 仅 0.0004, 但 REAGG 轴未与 HCG 形成正协同破顶 — 与 CCP×HCG 负交互形态不同, 是"接近但持平"而非"有害"
  - 对后续实验设计的建议: M80 (REAGG + 级联正确重聚合 × HCG, 修复链 2×2 满格) 正在 gpu0 续跑; 若 M80 > 0.5008 则级联修复链有增益; 未破顶仍等待 token 质量轴 (CTF) 或 query 调制/多层注入 (QMOD/MLAY) 突破

## 6. Crash Info (if crashed)
  - 无 crash; 正常 early-stop
  - 注: 2026-08-10 12:03 曾 resume (server-4 external fineweb-edu resource stall 后重启, 与 M62/M63 同因), 最终仍由 _120314.log 跑至 ep24 早停
================================================================================
