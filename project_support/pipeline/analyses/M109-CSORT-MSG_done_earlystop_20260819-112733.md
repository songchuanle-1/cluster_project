================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M109-CSORT-MSG | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M109-CSORT-MSG
  - Config: configs/Quard/csort_msg/model_base1_quard2_c2f_enc_lite_posA_l1_csort_msg.yaml
  - Server: server-4 | GPU: 1
  - Started: ~2026-08-18 22:38 | Finished: 2026-08-19 08:37:13 | Duration: ~10h
  - State: done_earlystop (no_improve=11/10, monitor kill PID=394754)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5010 | ~12/22  |
  | Acc@50   | ~0.553 | (est.)  |
  | spmIOU   | ~0.460 | (est.)  |

## 3. Convergence Summary
  - Best first reached at: ~epoch 12
  - Subsequent no_improve epochs: 10 (早停)
  - 收敛形态: 快速上升后震荡平台, 与 CTF-HCG 族典型形态一致

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0116 (有效)
  - vs champion M95-CTF-HCG-CSORT (seed1999=0.5020): γ = -0.0010 (持平, 在 seed 方差内)
  - vs CTF-HCG 基准 M81 (seed1999=0.5012): γ = -0.0002 (完全持平)
  - vs CSORT 标准位置 (M95=0.5020, seed1999): message 级 CSORT -0.0010,
    表明 CSORT 的应用位置不影响效果量级, 两者均在 seed 方差内

## 5. Conclusion
  - 结论: [持平] — message 级 CSORT 与标准 CSORT 效果相当 (0.5010 vs 0.5020),
    均在 seed 方差 ±0.004~0.007 内, 不改变 CSORT 机制无效的整体判断
  - 解释: 将 CSORT 从 cluster token 级移到 message (readback) 级, 不改变效果量级。
    结合 CSORT 跨 seed 证伪证据 (3/4 seed 负增益), 0.5010 仍归因 CTF-HCG 基底 + seed 有利性。
    变体本身有价值 (message 级 orth 是新位置), 但机制前提 (CSORT 有效) 已被否定。
  - 对后续实验设计的建议: CSORT 应用位置不再是关键变量, 轴正式关闭。

## 6. Crash Info (if crashed)
  - N/A
================================================================================
