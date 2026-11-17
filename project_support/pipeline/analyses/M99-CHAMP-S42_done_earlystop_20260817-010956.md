================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M99-CHAMP-S42 | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M99-CHAMP-S42
  - Config: configs/Quard/champ_s42/model_base1_quard2_c2f_enc_lite_posA_l1_champ_s42.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-16 03:09:51 | Finished: 2026-08-17 01:07:24 | Duration: ~22h
  - State: done_earlystop (no_improve=11/10 ≥ patience=10, monitor kill PID=3314894)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4930 | 19/25   |
  | Acc@50   | 0.547  | 19/25   |
  | spmIOU   | 0.457  | 19/25   |
  (序列: 0.334, 0.373, 0.400, 0.432, 0.435, 0.447, 0.462, 0.474, 0.471, 0.471,
          0.483, 0.488, 0.490, 0.484, 0.490, 0.491, 0.492, 0.491, 0.493, 0.490,
          0.487, 0.484, 0.488, 0.489)

## 3. Convergence Summary
  - Best first reached at: epoch 19
  - Subsequent no_improve epochs: 6 (ep20-25 均未刷新, 早停聚合 no_improve=11/10)
  - Final epoch best: mIoU=0.4890 vs historical best=0.4930
  - 收敛形态: 平稳爬升 (ep1-8: 0.334→0.474) → 平台震荡 (ep9-19: 0.471-0.493
    区间 11 次验证缓慢上探) → 回落 (ep20 后 0.487-0.490 不再刷新)

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0036 (有效但弱, context 收益保留)
  - vs champion (M95-CTF-HCG-CSORT=0.5020): γ = -0.0090 (跨 seed 显著回落)
  - vs M95 champion seed 对照 (M95 seed1999=0.5020 vs M99 seed42=0.4930):
    seed 波动 -0.0090, 说明 champion 的 seed 敏感性高
  - vs M100-CHAMP-S123 (running, 21/50, Best=0.4980): 当前 M99 落后 +0.0050

## 5. Conclusion
  - 结论: [失败] — champion 基底 seed=42 复现 0.4930, 未破顶且落后 champion 0.009
  - 解释: champion (posA_l1 基底) 在 seed=42 下仅 0.4930, 与 seed1999=0.5012/M95=0.5020
    差 0.009 — 说明 posA_l1 champion 的 mIoU 高度依赖 seed, 破顶观测 (M95) 可能是
    seed1999 有利抽样而非机制稳定增益。champion 基线跨 seed 稳定性未达破顶条件。
  - 对后续实验设计的建议: 继续跑 M100(seed123) 与 M101(seed2026) 补齐 champion
    seed 面。若跨 seed 均值仍 <0.50, 需在 champion 基底上寻找更鲁棒的结构性机制
    而非依赖单一 seed 幸运抽样。CSORT 族 (M103-M106) 待同 seed 对照验证其是否
    在 champion 基底上提供稳定增量。

## 6. Crash Info (if crashed)
  - 无 crash。正常早停。
================================================================================
