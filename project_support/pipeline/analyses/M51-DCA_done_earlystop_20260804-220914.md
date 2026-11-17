================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M51-DCA | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M51-DCA
  - Config: configs/Quard/dca/model_base1_quard2_c2f_enc_lite_posA_l1_dca.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-04 04:03:48 | Finished: ~2026-08-04 21:55 (early stop @ ep25) | Duration: ~18h
  - State: done_earlystop (正常早停: "Early stopping at epoch 25: no improvement for 10 epochs (best=0.4893)")

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4893 | 25      |
  | Acc@50   | 0.541  | ~25     |
  | spmIOU   | 0.448  | ~25     |
  (来源: 远程日志 Val 序列 + experiments.csv 归档)

## 3. Convergence Summary
  - Best first reached at: epoch ~20-25 (0.4893)
  - Subsequent no_improve epochs: 10 (early-stop at epoch 25)
  - Final epoch best: mIoU=0.4893 vs historical best=0.4893
  - 收敛形态: 缓慢爬升后平台, best 后 10 ep 未刷新 → 正常早停, 进程自然退出 (非 crash)

## 4. Comparison
  - vs baseline (model_base1, 0.4894): γ = -0.0001 (持平, 几乎无收益)
  - vs champion (posA_l1/DRP, 0.5012): γ = -0.0119 (失败, 未破 ceiling)
  - vs 同类聚合变体: M50-DGC(0.4913, diff-gated readback), M48-BIL(0.4919),
    M45-NCR(0.4980) — DCA 与聚合质量其他尝试一样低于 champion
  - 机制: dual pooling (mean + max → proj) 替换 mean-only 聚合

## 5. Conclusion
  - 结论: [失败] — dual pooling 聚合未带来增益
  - 解释: DCA 用 mean+max 双分支聚合 cluster token, best 0.4893 ≈ baseline, 远低于
    champion 的纯 mean 聚合 (0.5012)。说明 cluster token 表示层面, mean 池化仍是最优;
    max 分支引入的极端信号对 context 回读无独立收益。
  - 对后续实验设计的建议: 聚合轴仍在测 CCR(级联精炼)/VAC(方差)/SAC(空间嵌入) —
    DCA 的失败偏向证伪"双分支极端信号聚合"。若 CCR/VAC/SAC 也 < champion, 聚合轴
    与 readback expressiveness 轴一并闭合, 剩余未测空白收敛到 message 构造
    (M63-PSR 已入队) 与融合机制 (SCF/SCT 在队列)。

## 6. Crash Info
  - Error type: 无 (正常 early-stop 退出, 进程 PID 文件标记 DEAD, 非 crash)
  - 说明: 本 tick monitor 首见进程消失 (deathwatch 1/3), 拉日志确认 "Early stopping
    at epoch 25" → 判定 done_earlystop, 不按 stopped_unknown 处理。
================================================================================
