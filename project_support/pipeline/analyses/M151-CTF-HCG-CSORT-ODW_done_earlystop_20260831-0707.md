================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M151-CTF-HCG-CSORT-ODW | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M151-CTF-HCG-CSORT-ODW
  - Config: configs/Quard/ctf_hcg_csort_odw/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_odw.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-30 15:10 | Finished: 2026-08-31 07:07 | Duration: ~16h
  - State: done_earlystop (no_improve=11/10, monitor kill PID=906859)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4970 | 21/50   |
  | Acc@50   | 0.551  | 21      |
  | spmIOU   | 0.461  | 21      |
  (best.pth 保存于 log 序列 (mIOU: 0.497 / Acc_50: 0.551 / spmIOU: 0.461)。近5次验证: 0.458/0.493/0.455/0.495/0.458)

## 3. Convergence Summary
  - Best first reached at: ~epoch 21 (log "save best pth" 序列, mIOU 0.494→0.497 在 ep~20-21 冲顶)
  - Subsequent no_improve epochs: 11 (early-stopped by monitor, patience=10)
  - Final epoch best: mIoU=0.4970 vs historical best=0.4970
  - 收敛形态: 前 14 ep 训练平台 0.458-0.493 震荡, ep~20-21 冲顶 0.497, 之后 0.455-0.495 反复无刷新, 11 ep 未破 best

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0076 (有效, 但幅度 < CSORT 结构 0.0126)
  - vs champion (M95-CTF-HCG-CSORT 0.5020): γ = -0.0050 (未破顶)
  - vs M150-OWC (同批软约束对照, 0.4920): γ = +0.0050 (硬约束略优于软约束, 但均低于 champion)
  - vs M95-CSORT 纯结构 (0.5020): ODW 在 champion 上叠加正交分解写回硬约束 loss 反而掉 0.0050
    → **正交写回 (软/硬) 作为额外 loss 项均无独立增益**

## 5. Conclusion
  - 结论: [失败] (对 champion 而言)
  - 解释: M150 分析预言 — "若 ODW 超过 0.5020 说明硬约束路径可能不同; 若同水平则整条 OWC/ODW 轴关闭" — 现证实: ODW 硬约束正交分解写回 0.4970 < champion 0.5020 (γ=-0.0050)。软 (OWC=0.4920) 硬 (ODW=0.4970) 两条正交写回 loss 轴全部证伪。CSORT 的核心收益已完全由 champion 结构 (对称双向往推) 承载, 额外正交写回 loss 与信息路径无协同, 反引入优化干扰。
  - 对后续实验设计的建议: 关闭"正交写回 loss 项"方向 (OWC/ODW 轴终结)。CSORT 剩余探索集中在在队实验: M152-F1/M156-CP (尺度范围消融)、M154-GSC (全局尺度)、M155-RF (精炼 token 对齐)、M157-PMD (receiver 侧 message 去相关)、M158-PMD-SH (PMD 控制组)、M153-MFP (masked 重建组合)。

## 6. Crash Info (if crashed)
  - 无 crash。正常 early-stop。
================================================================================
