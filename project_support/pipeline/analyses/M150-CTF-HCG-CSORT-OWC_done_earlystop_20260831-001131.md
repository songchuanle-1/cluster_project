================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M150-CTF-HCG-CSORT-OWC | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M150-CTF-HCG-CSORT-OWC
  - Config: configs/Quard/ctf_hcg_csort_owc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_owc.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-30 12:07 | Finished: 2026-08-30 23:38 | Duration: ~11.5h
  - State: done_earlystop (no_improve=11/10, monitor kill PID=503744)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4920 | 20/50   |
  | Acc@50   | 0.542  | 20      |
  | spmIOU   | 0.456  | 20      |
  (best.pth 保存于 log "save best pth" 序列, monitor 序列计数 20. 近5次验证: 0.481/0.490/0.489/0.488/0.486)

## 3. Convergence Summary
  - Best first reached at: ~epoch 20 (log save best 于 0.477→0.479→0.482→0.474→0.490→0.492 序列, 最后刷新在 ep20)
  - Subsequent no_improve epochs: 11 (early-stopped by monitor, patience=10)
  - Final epoch best: mIoU=0.4920 vs historical best=0.4920
  - 收敛形态: 前 15 ep 在 0.477-0.482 平台, ep~18-20 冲顶 0.490-0.492, 之后 0.481-0.490 震荡无刷新

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0026 (勉强有效, 幅度显著小于 CSORT)
  - vs champion (M95-CTF-HCG-CSORT 0.5020): γ = -0.0100 (未破顶)
  - vs M151-ODW (同批硬约束对照, running 0.4870@ep12): OWC 软 loss 0.4920 略高于 ODW 当前值, 但均远低于 champion
  - vs CSORT 纯结构 (M95=0.5020): OWC 在 champion 上加正交写回 soft loss 反而掉 0.0100 → **正交写回作为额外 loss 项无独立增益**

## 5. Conclusion
  - 结论: [失败] (对 champion 而言)
  - 解释: OWC 假设 — "在 champion 写回路径上增加正交约束 loss (msg 与 feats 解相关) 能进一步提升去相关收益" — 被证伪: champion+正交写回 soft loss 从 0.5020 掉到 0.4920 (γ=-0.0100)。CSORT 的核心收益已完全由 champion 结构承载, 额外的正交写回 loss 项不与信息路径产生协同, 反而引入优化干扰。
  - 对后续实验设计的建议: 关闭"正交写回 loss 项"方向。M151-ODW (硬约束正交分解写回) 仍在跑, 若其超过 0.5020 则说明硬约束路径可能不同; 若同水平则整条 OWC/ODW 轴关闭。CSORT 剩余探索集中在在队实验: M152-F1/M156-CP (尺度范围消融)、M154-GSC (全局尺度)、M155-RF (精炼 token 对齐)、M157-PMD (receiver 侧 message 去相关)。

## 6. Crash Info (if crashed)
  - 无 crash。正常 early-stop。
================================================================================
