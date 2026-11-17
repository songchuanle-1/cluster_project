================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M88-QMOD-MLAY | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M88-QMOD-MLAY
  - Config: configs/Quard/qmod_mlay/model_base1_quard2_c2f_enc_lite_posA_l1_qmod_mlay.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-12 10:26 | Finished: 2026-08-13 23:16 | Duration: ~36.8h
  - State: done_earlystop (连续 11 次验证未刷新 best, kill PID=2165232)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4930 | ~16     |
  | Acc@50   | 0.546  | ~16     |
  | spmIOU   | 0.455  | ~16     |

## 3. Convergence Summary
  - Best first reached at: epoch ~16 (mIoU=0.4930, Acc@50=0.546, spmIOU=0.455)
  - Subsequent no_improve epochs: 11 (early-stopped at 22/50, patience=10)
  - Final epoch best: mIoU=0.4930 vs historical best=0.4930 (未再刷新)
  - 收敛形态: 前 8 epoch 快速上升 (0.319→0.480)，随后 0.46-0.49 平台震荡，
    序列 0.487/0.486/0.491/0.487/0.487... 均低于 best 0.4930，收敛平台明显，
    与 M85-QMOD 收敛形态完全一致 (同为 best~0.4930@~ep16)。

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0036 (有效)
  - vs current champion (posA_l1 0.5012): γ = -0.0082 (未破顶)
  - vs M85-QMOD (0.4930): γ = 0 (完全等价 — 叠加 MLAY 多层注入未带来额外增益)
  - vs M86-MLAY (running): 无终态数据; M88 的 0.4930 表明 QMOD×MLAY 组合 ≈ QMOD 单轴

## 5. Conclusion
  - 结论: [持平] (优于 baseline，但未破 champion 0.5012)
  - 解释: QMOD (cluster context 调制 decoder query，突破方向①) × MLAY
    (cluster_att_num_layers=2 多层注入，突破方向②) 组合 0.4930 与 M85-QMOD
    单轴完全等价 (γ=0)，说明两个方向**无正交互** — query 调制轴 + 多层注入轴
    均无破顶能力，且组合也不产生协同。这与 M86-MLAY (多层注入单轴) 的终态
    结果共同构成突破方向①②的证据。
  - 对后续实验设计的建议: QMOD 单轴与 QMOD×MLAY 组合均无破顶 → query 调制
    方向优先级下调；等待 M86-MLAY 终态确认多层注入单轴表现。CTF×HCG (M81=
    0.5012) seed 验证 (M89/M90/M91) 仍是当前最优先证据链项。
================================================================================
