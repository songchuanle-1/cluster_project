================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M81-CONS | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M81-CONS
  - Config: configs/Quard/cons/model_base1_quard2_c2f_enc_lite_posA_l1_cons.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-13 02:10 (checkpoint 20260813_021046) | Finished: 2026-08-14 03:07
  - State: done_earlystop (no_improve=11/10, 连续 11 epoch 未刷新 best, monitor kill)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4950 | 27      |
  | Acc@50   | 0.550  | 27      |
  | spmIOU   | 0.457  | 27      |

## 3. Convergence Summary
  - Best first reached at: epoch 27
  - Subsequent no_improve epochs: 11 (killed at patience=10)
  - Final trajectory: 前 20+ epoch 快速上升至 ~0.49，ep27 触顶 0.495 后验证序列在
    0.482-0.495 区间震荡 (末5: 0.4520/0.4830/0.4430/0.4820/0.4420)，判定早停。

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0056 (有效)
  - vs current champion (posA_l1 0.5012): γ = -0.0062 (未破顶)
  - vs M87-DET-CONS (0.4930 @20/50 running): 同量级，detail message 未见叠加增益

## 5. Conclusion
  - 结论: [有效] (优于 baseline，但显著低于 champion)
  - 解释: CONS (intra-cluster 一致性正则, 属于 consistency 型正则化) 使 cluster token
    间趋向一致，Best=0.4950。该方向未能逼近 champion 0.5012 — 与 QMOD(0.4930)、
    CCP 系列(0.4934-0.4952) 一致: 单纯的正则化/约束类机制在 champion 平台上无法破顶。
  - 对后续实验设计的建议: consistency 型机制 (CONS/QMOD/CCP) 不再单独投入;
    继续聚焦 CTF×HCG 组合轴 + 三轴协同 (M92 ORT 第三轴) 与多尺度多样性新轴。
================================================================================
