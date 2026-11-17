================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M117-CTF-HCG-BCF | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M117-CTF-HCG-BCF
  - Config: configs/Quard/ctf_hcg_bcf/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_bcf.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-21 17:17 | Finished: 2026-08-22 03:07 | Duration: ~10h
  - State: done_earlystop (monitor kill PID=805930, no_improve=11/10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4926 | ~18/50  |
  | Acc@50   | 0.550  | ~18/50  |
  | spmIOU   | 0.458  | ~18/50  |
  (log: "mIOU: 0.493. Acc_50: 0.550. Acc_25: 0.603 / spmIOU: 0.458. spAcc_50: 0.509. spAcc_25: 0.596")

## 3. Convergence Summary
  - Best first reached at: epoch ~18 (log save best at 23:58:54 on 08-21)
  - Subsequent no_improve epochs: 11 (monitor kill at 18/50)
  - Final epoch best: mIoU=0.4926 vs historical best 0.4926 — 平台震荡
  - 收敛形态: 快速爬升至 ~0.49 后平台, 后期无新 Best

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = +0.0032 (微效, 远低于 champion)
  - vs current champion (M95-CTF-HCG-CSORT = 0.5020): γ = -0.0094 (显著低)
  - vs CTF-HCG 家族真实均值 ~0.498: 低于家族均值 ~0.005
  - BCF (point→cluster reverse attention, 双向信息流) 在 CTF+HCG 基底上仅 +0.0032,
    与 M116-CGA 几乎同值 (0.4926/0.4926)

## 5. Conclusion
  - 结论: [持平/失败]
  - 解释: Bidirectional Context Flow (点→簇反向注意力 + 双向信息交换) 未带来增益,
    best 0.4926 ≈ 家族基线。与 CGA (M116=0.4926) 一起确认 encoder-side 的
    "信息交换方式" 微调均无法突破 ~0.49-0.50 平台, 佐证瓶颈在 writeback→decoder 通路。
  - 对后续实验设计的建议: BCF 轴关闭。当前 M118-LCC/M119-MFP 仍排队 (encoder-side),
    但历史上 encoder-side 无一破 0.501; 重点押注 decoder-side 直连 (M123-DCA/M124-DCM)
    验证 "writeback 有损瓶颈" 假设。
================================================================================
