================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M86-MLAY | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M86-MLAY
  - Config: configs/Quard/mlay/model_base1_quard2_c2f_enc_lite_posA_l1_mlay.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-13 23:13 | Finished: 2026-08-20 18:07 | Duration: ~6.8 天 (含间歇)
  - State: done_earlystop (no_improve=11/10 ≥ patience=10, monitor kill PID=1580735)
  - Cluster attention: legacy (无 ctf/hcg/csort 解相关), cluster_att_num_layers=2,
    cluster_message_type='context' (默认), seed=1999

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5010 | 25      |
  | Acc@50   | 0.556  | 25      |
  | spmIOU   | 0.464  | 25      |
  (log: "mIOU: 0.501. Acc_50: 0.556. Acc_25: 0.609 / spmIOU: 0.464. spAcc_50: 0.514. spAcc_25: 0.600")

## 3. Convergence Summary
  - Best first reached at: epoch 25
  - Subsequent no_improve epochs: 11 (early-stopped at ep26, 收敛平台)
  - mIoU 尾部序列: 0.496, 0.493, 0.491, 0.494, 0.500, 0.494, 0.500, 0.501(best), 0.498, 0.498, 0.494, 0.499
  - 收敛形态: 缓慢爬升至 ep25 达 0.501 后平台震荡, 10+ epoch 未刷新; 全程波动 ~0.49-0.50

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0116 (有效, 与 CTF+HCG 核心收益同级)
  - vs current champion (M95-CTF-HCG-CSORT=0.5020): γ = -0.0010 (持平, 差 1 个点内)
  - vs M81-CTF-HCG (0.5012, 1-layer ctf_hcg): γ = -0.0002 (持平)
  - vs M109-CSORT-MSG (0.5010): γ = 0.0000 (完全持平)
  - vs M96-CTF-HCG-2LAY (0.4940, ctf_hcg 2-layer): γ = +0.0070 — 关键对比
  - 关键解释: M96 (cluster_mode=ctf_hcg + 2层) 曾判定"多层注入退化",
    但 M86 (cluster_mode=legacy + 2层) 达到 0.5010 — 退化是 ctf_hcg 模式特有,
    非多层注入本身; legacy 2 层是多尺度 readback 的强基底

## 5. Conclusion
  - 结论: [有效]
  - 解释: 2 层 legacy 多尺度 cluster readback (无任何解相关机制) 即达 0.5010,
    与 champion M95 (csort+1层) 持平。这隔离出**多尺度 context 深度 (2层)** 是
    核心收益来源, ctf/hcg/csort 解相关仅边际 (+0.001 以内)。
    M96 的"2层退化"结论需修正为"ctf_hcg 模式下 2层退化"。
  - 对后续实验设计的建议:
    (1) MLay (2层 legacy) 是比 M95-csort 更"干净"的强基底 (无 seed-outlier 风险待验证);
    (2) 需 seed 对照 (M120) 确认 0.5010 非 seed-1999 伪影 — M95 已被证 seed-敏感;
    (3) 可与 detail message (D1=0.5003 独立有效) 组合 (M121) 测试是否叠加 → 目标 0.51

## 6. Crash Info (if crashed)
  - N/A (正常训练至早停)
================================================================================
