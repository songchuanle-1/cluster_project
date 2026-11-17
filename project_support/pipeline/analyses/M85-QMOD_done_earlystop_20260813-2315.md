================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M85-QMOD | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M85-QMOD
  - Config: configs/Quard/qmod/model_base1_quard2_c2f_enc_lite_posA_l1_qmod.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-12 10:27 | Finished: 2026-08-13 23:07 | Duration: ~36.7h
  - State: done_earlystop (no_improve=11/10, 连续 11 epoch 未刷新 best)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4930 | ~16     |
  | Acc@50   | 0.543  | ~16     |
  | spmIOU   | 0.457  | ~16     |

## 3. Convergence Summary
  - Best first reached at: epoch ~16 (mIoU=0.4930, Acc@50=0.543, spmIOU=0.457)
  - Subsequent no_improve epochs: 11 (early-stopped at patience=10, kill 22/50)
  - Final epoch best: mIoU=0.4930 vs historical best=0.4930 (未再刷新)
  - 收敛形态: 前 8 epoch 快速上升 (0.327→0.477)，随后 0.47-0.49 平台震荡，
    ep16 触顶 0.4930 后连续 6 次验证 0.487/0.487/0.487/0.488/0.482 均低于 best，
    判定早停。验证序列存在周期性回落(每 epoch 内 mIOU/spmIOU 交替), 收敛平台明显。

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0036 (有效)
  - vs current champion (posA_l1 0.5012): γ = -0.0082 (未破顶)
  - vs M88-QMOD-MLAY (running, best 0.4930): γ = 0 (当前等价, M88 尚在跑)
  - vs M65-HCG (0.5002): γ = -0.0072 (低于 HCG 正确交付)

## 5. Conclusion
  - 结论: [持平] (优于 baseline，但未破 champion 0.5012)
  - 解释: QMOD (cluster context 调制 decoder query，goal.json 突破方向①) 单轴
    0.4930 仅 +0.0036 vs baseline，未达到 champion 0.5012。query 调制轴单独
    无破顶能力 — 与 M88-QMOD-MLAY 当前 0.4930 等价，说明叠加 MLAY 也尚未带来
    增益（M88 尚在跑，待终态再判）。
  - 对后续实验设计的建议: QMOD 单轴方向优先级下调；等待 M88-QMOD-MLAY 终态
    判断 query 调制 × 多层注入是否有正交互。CTF×HCG (M81=0.5012) 种子验证
    (M89/M90/M91) 仍是当前最优先证据链项。
================================================================================
