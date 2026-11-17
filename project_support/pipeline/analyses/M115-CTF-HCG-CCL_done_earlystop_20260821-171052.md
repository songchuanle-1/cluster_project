================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M115-CTF-HCG-CCL | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M115-CTF-HCG-CCL
  - Config: configs/Quard/ctf_hcg_ccl/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_ccl.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-21 05:07:36 | Finished: 2026-08-21 17:07:27 | Duration: ~12h
  - State: done_earlystop (monitor kill PID=3382466, no_improve=11/10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4890 | ~22/50  |
  | Acc@50   | 0.541  | ~22/50  |
  | spmIOU   | 0.452  | ~22/50  |
  (metrics extracted from remote log line 140: mIOU 0.489, Acc_50 0.541, spmIOU 0.452;
   log pull failed → checkpoint 留远端, 数值经 ssh 读取 log 验证)

## 3. Convergence Summary
  - Best first reached at: epoch ~22 (log 峰值 mIOU 0.489, Acc50 0.541, spmIOU 0.452)
  - Subsequent no_improve epochs: 11 (monitor kill at 23/50)
  - Final epoch best: mIoU=0.4890 (line 140) vs last val 0.480/0.480 — 平台震荡, 未破顶
  - 收敛形态: 0.323(ep1) → 0.489(峰值) → 0.480 平台震荡, 后期无新 Best

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = -0.0004 ≈ 0 (持平)
  - vs current champion (M95-CTF-HCG-CSORT = 0.5020): γ = -0.0130 (失败)
  - vs CTF-HCG 家族真实均值 ~0.498 (M81=0.5012/M95=0.5020 为 seed-1999 outlier):
    低于家族均值 ~0.009

## 5. Conclusion
  - 结论: [持平/失败]
  - 解释: Cluster Contrastive Loss (InfoNCE cross-scale alignment aux loss, 促进
    cluster token 判别性) 在 CTF+HCG 基底上无收益 (0.4890 ≈ baseline), 且显著低于
    CTF-HCG 家族平台 (~0.498)。对比实验确认「多尺度 cluster context 收益来自
    context 回写通路而非 token 判别性增强」— 该辅助损失方向关闭。
  - 对后续实验设计的建议: CCL 作为 aux loss 方向关闭, 不再复现; 机制家族
    (CSORT/ORT/MEMBANK/SRL/CCL) 已覆盖「cluster token 质量增强」轴且全部关闭,
    与 goal.json 结论一致 — 收益在 context 交付通路 (CTF+HCG/detail/MLay) 与
    decoder 侧直连 (M123-DCA/M124-DCM) 上, 继续推进 decoder 侧证据。
================================================================================
