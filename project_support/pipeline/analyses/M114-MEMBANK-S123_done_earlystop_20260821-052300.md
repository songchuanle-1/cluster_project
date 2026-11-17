================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M114-MEMBANK-S123 | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M114-MEMBANK-S123
  - Config: configs/Quard/ctf_hcg_membank_s123/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_membank_s123.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-20 16:10 | Finished: 2026-08-21 04:37 | Duration: ~12.5h
  - State: done_earlystop (monitor kill PID=1758872, no_improve ≥ patience=10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5010 | 16      |
  | Acc@50   | 0.554  | 16      |
  | spmIOU   | 0.464  | 16      |
  (log: "mIoU : 0.5009114146232605 / mIOU: 0.501. Acc_50: 0.554. Acc_25: 0.608 / spmIOU: 0.464. spAcc_50: 0.516. spAcc_25: 0.601")

## 3. Convergence Summary
  - Best first reached at: epoch 16 (validation 2026-08-21 01:27)
  - Subsequent no_improve epochs: 6 (ep17-22: 0.495, 0.491, 0.494, 0.498, 0.499, ... 全部 < 0.5010)
  - 收敛形态: 前 16 epoch 稳步爬升 (0.489@ep? → 0.501@ep16), 随后回落平台,
    no_improve 达阈值早停。与 M110-MEMBANK (s1999=0.4954) / M112-MEMBANK-S42 (0.4890)
    对照: s123 是该轴三个 seed 中唯一触及 champion 水平的点

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0116 (有效)
  - vs current champion (M95-CTF-HCG-CSORT=0.5020): γ = -0.0010 (持平)
  - vs M81-CTF-HCG (0.5012): γ = -0.0002 (完全持平)
  - vs M110-MEMBANK (s1999=0.4954): γ = +0.0056 — seed 差异
  - vs M112-MEMBANK-S42 (0.4890): γ = +0.0120 — seed 差异显著
  - 关键解释: MEMBANK 轴跨 3 seed (1999/42/123) 均值为 (0.4954+0.4890+0.5010)/3 ≈ 0.4951,
    低于 champion 0.5012。s123 的 0.5010 是 seed 有利性伪影, 与 M95-CSORT 模式一致
    (seed-1999 outlier 0.5020, true mean ~0.498)

## 5. Conclusion
  - 结论: [持平] (seed 伪影, 轴不复活)
  - 解释: M114-s123 达 0.5010 但 M110-s1999=0.4954 / M112-s42=0.4890,
    三 seed 均值 0.4951 < champion。MEMBANK (跨 batch 记忆) 无稳健收益,
    s123 的高分是种子效应, 轴保持关闭。
  - 对后续实验设计的建议: 确认 MEMBANK 轴关闭 (3 seed 覆盖); 0.5010 的 s123
    偶然性进一步佐证 "~0.501 平台横跨所有 encoder-side 机制" 观察 —
    支持本轮 DCA (decoder-side) 方向设计
================================================================================
