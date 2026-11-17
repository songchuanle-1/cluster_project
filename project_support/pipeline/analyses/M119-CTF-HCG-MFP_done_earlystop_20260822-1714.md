================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M119-CTF-HCG-MFP | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M119-CTF-HCG-MFP
  - Config: configs/Quard/ctf_hcg_mfp/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_mfp.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-22 03:13:23 | Finished: 2026-08-22 17:08:26 (早停 kill) | Duration: ~14h
  - State: done_earlystop (monitor kill PID=2062141, no_improve=11/10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5020 | 15      |
  | Acc@50   | 0.557  | 15      |
  | spmIOU   | 0.467  | 15      |
  (Best 首次刷出于验证第 15 次; 之后 5+ 次验证在 0.493-0.497 平台)

## 3. Convergence Summary
  - Best first reached at: validation #15 (mIOU 0.502, Acc50 0.557, spmIOU 0.467)
  - Subsequent no_improve epochs: 11/10 (monitor kill)
  - Final epoch best: mIOU=0.5020 vs plateau 0.493-0.497
  - 收敛形态: 快速上升至第10次验证 ~0.494, 第15次刷 0.502 顶, 之后 5 次验证在
    0.493-0.497 平台无刷新 → 早停。序列与 champion M95 收敛形态高度一致。

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = +0.0126 (有效)
  - vs champion (M95-CTF-HCG-CSORT = 0.5020): γ = 0.0000 (持平, 同 seed 1999)
  - vs CTF-HCG base (M81 = 0.5012): γ = +0.0008 (持平)
  - 对照轴: 同为 encoder-side 辅助损失 — CCL=0.4890, CGA=0.4926, BCF=0.4926,
    SRL=0.4912 均显著掉点; MFP 是唯一不伤(但也不涨)的 encoder-side 机制

## 5. Conclusion
  - 结论: [持平] — MFP 在 seed 1999 复现 champion 水平 (0.5020), 但未破 ~0.501 平台
  - 解释: 特征级 mask 重建辅助损失既不伤害主任务也不带来增量。考虑到已知的
    seed-1999 优势模式 (CSORT=0.5020 被归因种子效应, true mechanism mean ~0.498),
    MFP=0.5020 很可能是同一种子红利而非机制突破。区别于 CCL/CGA/BCF/SRL
    (掉到 0.489-0.493), MFP 辅助损失零伤害 — 这是它唯一的正面信号。
  - 对后续实验设计的建议: ① 加 MFP seed 对照 (S42/S123) 判定 0.5020 是否机制性
    (若 S42 也 ~0.50 则是真实机制, 可与 decoder 访问组合); ② 若 seed 对照确认
    seed 效应 → 关闭 MFP 轴, 聚焦 decoder-access 轴 (M123-DCA/M124-DCM 已启动)

## 6. Crash Info
  - Error type: N/A (早停 kill, 非 crash)
  - Auto-fix attempt: N
================================================================================
