================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M89-CTF-HCG-R2 | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M89-CTF-HCG-R2
  - Config: configs/Quard/ctf_hcg_r2/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_s42.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-14 00:10:57 (queue_push PID=1672532, server-6 空闲槽位补推) | Finished: 2026-08-16 02:07:32
  - Duration: ~50h (含周末中断/调度空隙)
  - State: done_earlystop (no_improve=11/10, monitor kill PID=1672532)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4980 | 29      |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (注: 日报 2026-08-16 记录"日志→拉取失败（checkpoint 留远端）", Acc50/spmIOU 未能回拉;
   历史同 seed 系 M91-HCG-R2 (s42) 参考 Acc50=0.550 spmIOU=0.459)

## 3. Convergence Summary
  - Best first reached at: epoch 29 (mIoU 0.4980)
  - Subsequent no_improve epochs: 11 (monitor kill, patience=10)
  - Final epoch best: mIoU=0.4980 vs historical best=0.4980
  - 收敛形态: 末 5 验证序列 0.4520/0.4870/0.4490/0.4870/0.4480 — 大幅震荡 (峰值~0.487 vs
    best 0.498 差 0.011), 平台期波动剧烈, 未再刷新, 判定早停

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0086 (有效)
  - vs current champion (posA_l1 0.5012): γ = -0.0032 (未破顶)
  - vs M81-CTF-HCG (0.5012, seed1999): γ = -0.0032 — **同一 CTF×HCG 配置换 seed=42
    掉点 0.0032**, 复现性再确认
  - vs M90-CTF-HCG-S3 (0.4940, seed123): γ = +0.0040 (s42 > s123)
  - vs M91-HCG-R2 (0.4963, HCG alone seed42): γ = +0.0017 (CTF×HCG > HCG alone 同 seed)

## 5. Conclusion
  - 结论: [有效] (优于 baseline +0.0086) 但 [未破顶], 且 seed 敏感性再确认
  - 解释: M89 是 M81-CTF×HCG (0.5012, seed1999) 的 seed=42 复现检查, 结果 0.4980 低于
    M81 达 0.0032。与 M90 (seed123 掉 0.0072)、M91 (HCG seed42 掉 0.0039) 合并看,
    **seed=1999 的高分系统性含 seed 有利性**: CTF×HCG 轴真实水平 ~0.494-0.498,
    champion 架构在 seed1999 下普遍 ~0.5005-0.5012 的观点进一步强化。
  - 对后续实验设计的建议: (1) M95-CTF-HCG×CSORT (seed1999)=0.5020 首个>champion 观测,
    但 +0.0008 落在 seed 方差 (±0.004-0.007) 内, 单点不能判定 CSORT 真实破顶;
    已设计 M103/M104 (CSORT seed2026/42) 与 M102/M89 构成同 seed 对照, 剥离 seed 方差;
    (2) 本 tick 队列深度 5<6, 已按 08-16 02:15 exp_design 补齐至 7;
    (3) 若 M103/M104 无一致正增量, CSORT 归为 seed 有利性, 破顶转多层注入 (M86/M96)。

## 6. Crash Info (if crashed)
  - 无 crash。本实验为早停终止 (no_improve=11>=10)。中断原因主要为周末调度空隙,
    非代码错误。
================================================================================
