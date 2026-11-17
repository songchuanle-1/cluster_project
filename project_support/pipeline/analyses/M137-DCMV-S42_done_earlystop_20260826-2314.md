================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M137-DCMV-S42 | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M137-DCMV-S42
  - Config: configs/Quard/ctf_hcg_dcmv_s42/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_dcmv_s42.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-26 07:09 (queue_push, 承接 M135-DCM-S42 早停释放的 gpu1)
  - Finished: 2026-08-26 23:07 (早停 kill PID=2799039) | Duration: ~16h
  - State: done_earlystop (no_improve=11/10 ≥ patience=10, monitor kill)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4920 | 24/50   |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (日志拉取失败, checkpoint 留远端; 指标来源 pipeline_monitor 日志尾解析)
  monitor 近5次验证序列: 0.4470, 0.4870, 0.4490, 0.4900, 0.4520 — Best 后高位震荡

## 3. Convergence Summary
  - Best first reached at: epoch 24 (mIoU=0.4920)
  - Subsequent no_improve epochs: 11/10 (monitor kill)
  - Final epoch best: mIoU=0.4920 (24/50) vs historical best=0.4920
  - 收敛形态: 前 10 ep 快速上升后 0.487-0.492 平台震荡, 峰值 0.4920 未再刷新,
    与 DCMV 系列 (M133=0.4950) 同形态但平台顶更低

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = +0.0026 (弱有效, 刚过 baseline)
  - vs current champion (M95-CTF-HCG-CSORT = 0.5020): γ = -0.0100
  - vs M133-DCMV (seed=1999, 0.4950): γ = -0.0030 — seed 42 掉点 0.003
  - vs M124-DCM (qla 语言通路, 0.5010): γ = -0.0090
  - vs M135-DCM-S42 (qla×seed42, 0.4970): γ = -0.0050
  - 关键对照 {qla,qia}×{cluster KV} 矩阵 (M133/M134/M124 补格完成):
    qia 视觉通路 M137=0.4920 < M133=0.4950, 均远低于 qla 语言通路 M124=0.5010

## 5. Conclusion
  - 结论: [失败/弱] — M137 = DCMV (qia 视觉通路) × seed=42 = 0.4920,
    仅 +0.0026 vs baseline, 低于 seed=1999 的 M133=0.4950 掉点 0.0030
  - 解释: M137 是 M133-DCMV 的 seed=42 复现控制。结果 0.4920 确认两件事:
    ① qia 视觉通路访问 cluster KV 无判别性增益 (与 M133/M134 结论一致) —
       访问 cluster context 的收益集中在 qla 语言通路 (M124=0.5010);
    ② DCMV 平台顶含 seed-1999 成分 (seed 42 掉点 0.003), 与 MFP 3-seed 矩阵、
       M135-DCM-S42 (掉点 0.004) 的 seed 敏感性同型。
    综合: qia/DCMV 轴已双 seed 确认弱 (M133=0.4950/M137=0.4920), 关闭。
  - 对后续实验设计的建议:
    ① {qla,qia}×{cluster KV} 矩阵双 seed 补格完成 — DCMV/qia 轴正式关闭,
       不再设计该方向变体;
    ② 0.501-0.502 平台瓶颈确认在 cluster token 自身信息量 (非通路数量) —
       当前唯一未证伪假设是 loss 监督轴 (M140-CLICA 判别 / M141-CSIC 一致 /
       M142 双监督), 均已 queued;
    ③ M139-MLAY-DUAL-LEGACY 本 tick 推送, M138/M120/M121 running —
       叠加组合轴预期同样不叠加, 主要看 loss 轴是否打开新信息路径;
    ④ 若 loss 轴三变体 (M140/M141/M142) 全部 ≈0.501 → 结构与 loss 监督轴
       双双饱和, 需范式级新方向 (记为 question, 暂停自主设计, 等用户拍板)。

## 6. Crash Info
  - Error type: N/A (早停 kill, 非 crash)
  - Auto-fix attempt: N
================================================================================
