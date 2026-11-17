================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M116-CTF-HCG-CGA | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M116-CTF-HCG-CGA
  - Config: configs/Quard/ctf_hcg_cga/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_cga.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-21 07:07 | Finished: 2026-08-22 03:07 | Duration: ~20h
  - State: done_earlystop (monitor kill PID=3692574, no_improve=11/10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4926 | ~23/50  |
  | Acc@50   | 0.547  | ~23/50  |
  | spmIOU   | 0.457  | ~23/50  |
  (log: "mIOU: 0.493. Acc_50: 0.547. Acc_25: 0.595 / spmIOU: 0.457. spAcc_50: 0.508. spAcc_25: 0.588")

## 3. Convergence Summary
  - Best first reached at: epoch ~22-23 (log save best at 22:24:33 on 08-21)
  - Subsequent no_improve epochs: 11 (monitor kill at 23/50, no_improve=11/10)
  - Final epoch best: mIoU=0.4926 vs historical best 0.4926 — 平台震荡
  - 收敛形态: 缓慢爬升至 ~0.49 平台, 后期无新 Best

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = +0.0032 (微效, 远低于 champion)
  - vs current champion (M95-CTF-HCG-CSORT = 0.5020): γ = -0.0094 (显著低)
  - vs CTF-HCG 家族真实均值 ~0.498: 低于家族均值 ~0.005
  - CGA (cluster graph attention, 簇间图传播) 在 CTF+HCG 基底上仅 +0.0032

## 5. Conclusion
  - 结论: [持平/失败]
  - 解释: Cluster Graph Attention (簇间图注意力传播) 未提升 context 质量,
    best 0.4926 ≈ 家族基线 (0.4894-0.498)。与 CCL (M115=0.4890) 一起确认
    "cluster token 内部质量增强" 轴 (contrastive/graph 传播) 无独立收益。
  - 对后续实验设计的建议: CGA 轴关闭。token 质量轴 (CCL/CGA) 已覆盖且失败,
    与 goal.json 结论一致 — 收益在 context 交付通路 (CTF+HCG/detail/MLay) 与
    decoder 侧直连 (M123-DCA/M124-DCM) 上, 继续推进 decoder 侧证据。
================================================================================
