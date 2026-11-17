================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M84-DET-CTF-HCG | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M84-DET-CTF-HCG
  - Config: configs/Quard/det_ctf_hcg/model_base1_quard2_c2f_enc_lite_posA_l1_det_ctf_hcg.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-12 18:51 | Finished: 2026-08-13 12:07 | Duration: ~17h16m
  - State: done_earlystop (no_improve=13/10, 连续 13 epoch 未刷新 best)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4990 | ~27     |
  | Acc@50   | 0.552  | ~27     |
  | spmIOU   | 0.462  | ~27     |

## 3. Convergence Summary
  - Best first reached at: epoch ~27
  - Subsequent no_improve epochs: 13 (early-stopped at patience=10)
  - Final epoch best: mIoU=0.4990 vs historical best=0.4990 (未再刷新)
  - 收敛形态: 前 20 epoch 快速上升 (0.178→0.499)，~ep27 触顶后进入平台震荡，后续验证序列
    0.492/0.492/0.486/0.488/0.486/0.487/0.450/0.486/0.447/0.487/0.448 均低于 best，判定早停。

## 4. Comparison
  - vs baseline (model_base1): γ = +0.0096 (有效)
  - vs current champion (posA_l1 0.5012): γ = -0.0022 (略低, 未超 champion)
  - vs M82-DET-CTF (0.4989): γ = +0.0001 (等价)
  - vs M81-CTF-HCG (0.5012): γ = -0.0022 (低于 CTF×HCG 单独)
  - vs M83-DET-REAG-CASC (0.4910): γ = +0.0080 (有效)

## 5. Conclusion
  - 结论: [持平] (优于 baseline，但与单组件组合等价/略低)
  - 解释: CTF×HCG×detail 三维满格组合 = 0.4990，不高于 M81-CTF-HCG 单独 (0.5012)。
    detail message 在 CTF×HCG 之上无叠加增益 — 与 E4 (residual+detail 无协同)、
    M59 (detail+QSF 无增益) 的证据链一致: detail 单独有效 (D1=0.5003)，
    但与其它机制组合时被稀释，不产生正交互。
  - 对后续实验设计的建议: 不再在 detail 与其它机制的组合方向上投入。
    CTF×HCG (M81=0.5012) 已达 champion-tie，种子验证 (M89/M90/M91) 是当前最优先证据链项。
================================================================================
