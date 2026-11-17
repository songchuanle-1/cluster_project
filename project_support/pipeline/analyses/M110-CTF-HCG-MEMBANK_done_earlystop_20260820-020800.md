================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M110-CTF-HCG-MEMBANK | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M110-CTF-HCG-MEMBANK
  - Config: configs/Quard/ctf_hcg_membank/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_membank.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-19 11:44:49 | Finished: 2026-08-20 02:07:32 | Duration: ~14.5h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4950 | ~10     |
  | Acc@50   | N/A    | —       |
  | spmIOU   | N/A    | —       |

## 3. Convergence Summary
  - Best first reached at: epoch ~10 (estimated from oscillation pattern)
  - Subsequent no_improve epochs: 13 (early-stopped at epoch 23/50)
  - Oscillation pattern: 0.4480, 0.4840, 0.4460, 0.4830, 0.4480 (large amplitude ~0.038)
  - Convergence shape: early peak then severe oscillation, unable to stabilize above best

## 4. Comparison
  - vs baseline (model_base1, 0.4894): γ = +0.0056 (marginally positive)
  - vs champion (M95-CTF-HCG-CSORT, 0.5020): γ = -0.0070 (below champion)
  - vs M81-CTF-HCG (0.5012, base architecture): γ = -0.0062
  - vs M109-CSORT-MSG (0.5010, latest readback improvement): γ = -0.0060

## 5. Conclusion
  - 结论: [持平]
  - 解释: Memory bank (cross-batch EMA prototype update) 仅带来 +0.0056 vs baseline, 且训练极不稳定 (振幅~0.038), 远未接近 champion. 跨 batch 记忆机制在当前 cluster context 框架下未提供有效增益, 可能因 EMA 更新频率与 batch 间分布差异导致不稳定.
  - 对后续实验设计的建议: MEMBANK 方向搁置. seed 对照变体 (M112-S42, M114-S123) 仍在队列中, 可视作 negative control 确认. 如果 seed 对照也 < baseline, 正式关闭 MEMBANK 轴.

## 6. Crash Info (if crashed)
  - N/A — clean early stop
================================================================================
