================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M139-MLAY-DUAL-LEGACY | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M139-MLAY-DUAL-LEGACY
  - Config: configs/Quard/mlay_dual_legacy/model_base1_quard2_c2f_enc_lite_posA_l1_mlay_dual_legacy.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-26T23:13:19 | Finished: 2026-08-27T21:07:24 | Duration: ~22h
  - State: done_earlystop (monitor kill PID=1126555, no_improve=11/10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4880 | 18/50   |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (Acc50/spmIOU 缺失: 日志留在远端, monitor 仅记录 mIoU)

## 3. Convergence Summary
  - Best first reached at: epoch 18 (0.4880)
  - Subsequent no_improve epochs: 11 (early-stopped at 18/50)
  - Final epoch best: mIoU=0.4880 vs historical best=0.4880
  - 收敛形态: 0.40-0.49 区间爬升, ep18 达 0.4880 后 11 epoch 未刷新, 平台提前

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = -0.0014 (低于 baseline, 失败)
  - vs current champion (M95-CTF-HCG-CSORT=0.5020): γ = -0.0140
  - vs M138-MLAY-DUAL (ctf_hcg base, 缺陷版)=0.4990: γ = -0.0110
  - vs M86-MLAY (legacy 2层单独)=0.5010: γ = -0.0130
  - vs M126-MLAY-DCM (legacy 2层 x DCM qla)=0.4980: γ = -0.0100
  - 前置: M139 为 M138 的 base 修正版 (legacy 2层 vs ctf_hcg 2层),
        满强度 {MLay 2层 legacy}×{DUAL qla+qia} 组合天花板格

## 5. Conclusion
  - 结论: [失败] — {MLay 2层 legacy}×{qla+qia 双通路} 组合 0.4880,
        不仅不叠加, 且低于 baseline 0.4894 和缺陷版 M138 0.4990。
  - 解释: 修正 base 后组合仍不叠加, 甚至比 ctf_hcg base 版本更低 0.011;
        与 M125/M126/M136/M138 通路组合不叠加模式一致 — {MLay 2层} 与
        {cluster KV 直读双通路} 两条机制在信息流上重叠, 无正交增益。
        M139 排除"base 缺陷导致误判"的可能, 组合轴判定正式成立。
  - 对后续实验设计的建议: 关闭 {MLay 2层}×{双通路} 组合轴 (已 5 次确认不叠加,
        不再投入)。当前开放方向为 loss 监督轴 (M141-CSIC/M142-CLICA-CSIC/M143-OBJG/
        M144-LQA) 与 champion 获胜机制扩展 (M145-CSORT-ALL), 等待终态结果。
================================================================================
