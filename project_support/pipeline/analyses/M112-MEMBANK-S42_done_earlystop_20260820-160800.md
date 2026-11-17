================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M112-MEMBANK-S42 | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M112-MEMBANK-S42
  - Config: configs/Quard/ctf_hcg_membank_s42/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_membank_s42.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-20 02:37:15 | Finished: 2026-08-20 16:07:28 | Duration: ~13.5h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4890 | 17      |
  | Acc@50   | 0.542  | 17      |
  | spmIOU   | 0.453  | 17      |

## 3. Convergence Summary
  - Best first reached at: epoch 17
  - Subsequent no_improve epochs: 6 (monitor killed at ep23 with no_improve=11/10)
  - mIoU series: 0.312, 0.376, 0.397, 0.426, 0.446, 0.451, 0.456, 0.456, 0.475, 0.474, 0.484, 0.483, 0.483, 0.482, 0.488, 0.477, **0.489**, 0.480, 0.484, 0.478, 0.483, 0.479
  - 收敛形态: 快速上升至 ep15 后进入 0.477-0.489 震荡平台, ep17 达峰值后 6 epoch 未刷新 Best

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = -0.0004 (持平/微弱低于 baseline)
  - vs current champion (M95-CTF-HCG-CSORT=0.5020): γ = -0.0130 (显著低于 champion)
  - vs M110-MEMBANK seed=1999 (0.4954): γ = -0.0064 (seed=42 低于 seed=1999)
  - vs CTF-HCG base (M81/M89≈0.5012): γ = -0.0122 (大幅低于基础 CTF-HCG)

## 5. Conclusion
  - 结论: [失败]
  - 解释: Memory bank seed=42 复现实验 mIoU=0.4890 甚至微弱低于 baseline 0.4894。与 M110 seed=1999 (0.4954) 相比下降 0.0064, 显示 memory bank 不仅无效且存在显著 seed 敏感性。两个 seed 均值 = 0.4922, 仍低于 baseline, 充分证明 memory bank 方向无效。
  - 对后续实验设计的建议: Memory bank 方向已彻底否定 (2 seeds 均失败)。M114 seed=123 作为第三个对照正在运行, 但方向已确定, 仅补充统计证据。建议后续将资源集中在 CCL/CGA/BCF/LCC 等结构性机制上。
================================================================================
