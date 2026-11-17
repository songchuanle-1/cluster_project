================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M87-DET-CONS | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M87-DET-CONS
  - Config: configs/Quard/det_cons/model_base1_quard2_c2f_enc_lite_posA_l1_det_cons.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-13 12:09 (log train_..._det_cons_20260813_120909.log) | Finished: 2026-08-14 06:07
  - State: done_earlystop (no_improve=11/10, 连续 11 epoch 未刷新 best, monitor kill PID=2941817)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4930 | 24      |
  | Acc@50   | 0.546  | 24      |
  | spmIOU   | 0.457  | 24      |

## 3. Convergence Summary
  - Best first reached at: epoch 24
  - Subsequent no_improve epochs: 11 (killed at patience=10)
  - Final trajectory: 前 20 epoch 单调上升至 ~0.49 (0.421→0.493), ep24 触顶 0.493 后
    验证序列在 0.480-0.493 区间缓慢下滑震荡 (末5: 0.4480/0.4800/0.4430/0.4830/0.4450),
    判定早停。

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0036 (有效)
  - vs current champion (posA_l1 0.5012): γ = -0.0082 (未破顶)
  - vs M81-CONS (0.4950, CONS alone): γ = -0.0020 — detail message 在 CONS 基底上无叠加增益
  - vs M84-DET-CTF-HCG (0.4990, detail × CTF×HCG): 同向 — detail message 组合普遍无正协同

## 5. Conclusion
  - 结论: [有效] (优于 baseline，但显著低于 champion)
  - 解释: det_cons = CONS (intra-cluster 一致性正则) × detail 残差 message。Best=0.4930
    不仅未破 champion 0.5012, 且低于 CONS alone (M81=0.4950) — detail message 轴与
    consistency 型机制负交互。与 QMOD(0.4930)/CCP(0.4934-0.4952) 一致: 约束/一致性/
    传播类机制在 champion 平台上无法破顶, 且与 detail 无正协同。
  - 对后续实验设计的建议: consistency 型机制 (CONS/QMOD/CCP) 不再单独投入,
    detail message 轴也不再与约束类机制组合; 继续聚焦 CTF×HCG 组合轴 + 三轴协同
    (M92 ORT 第三轴, 已修梯度断流) + 跨尺度多样性新轴 (M95-CSORT)。
================================================================================
