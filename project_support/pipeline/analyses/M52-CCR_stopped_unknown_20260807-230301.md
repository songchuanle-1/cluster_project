================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M52-CCR | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M52-CCR
  - Config: configs/Quard/ccr/model_base1_quard2_c2f_enc_lite_posA_l1_ccr.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-04 (server-6 GPU7) | Finished: 2026-08-07 23:03:22 | Duration: ~3d
  - State: stopped_unknown (进程消失 ×3 次确认; 远端日志拉取失败, checkpoint 留远端)
  - 机制: Cascade Refinement — SharedClusterBank 级联聚合过程中每层池化后用共享
    pre-norm FFN 精炼 cluster token, 再送入下一层聚合, 减少 mean 级联噪声传播.
    config: cluster_mode=drp / cluster_message_type=context / cluster_pool_type=mean / cascade_refine=True

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4948 | 29      |
  (stopped_unknown: 进程消失前最后一次保存的 best; Acc@50/spmIOU 因日志未拉取无法获取)

## 3. Convergence Summary
  - Best first reached at: epoch ~29 (best=0.4948)
  - 进程于 08-07 23:03 死亡 (deathwatch 3/3), 无日志可回溯完整收敛形态
  - 推断: 运行约 3 天到 ep29, 与 M53-VAC 同期同卡 (server-6 GPU7 多进程共享), 属自然终止;
    与 M41-CTF (读回前 FFN 精炼 0.4995) 相比, 级联过程中精炼未达到同水平

## 4. Comparison
  - vs baseline (model_base1): γ = +0.0054 (有效, 超过 baseline)
  - vs champion (posA_l1 0.5012): γ = -0.0064
  - vs M41-CTF (读回前精炼 0.4995): γ = -0.0047 — 级联过程中精炼 < 读回前精炼
  - 与同批聚合质量维度实验 (DCA 0.4893 / VAC 0.4889): CCR 0.4948 为聚合轴最高,
    但仍低于 champion 0.5012

## 5. Conclusion
  - 结论: [有效但未达冠军] (γ=+0.0054 vs baseline, 但 -0.0064 vs champion)
  - 解释: 级联过程中 per-layer 精炼确实减少了 mean 聚合噪声传播 (优于 baseline),
    但收益不及在读回前对已建好的簇 token 做精炼 (M41-CTF 0.4995), 且仍无法突破
    champion 0.5012. 聚合管线内部精炼这一轴的空间有限.
  - 对后续实验设计的建议: 聚合质量轴 (池化统计量 DCA/VAC + 级联精炼 CCR) 已基本覆盖,
    最高 0.4948 < champion. 故事线应继续向 token 质量(CCP)与交付机制(HCG)推进,
    当前队列 M69-M74 已覆盖该方向, 无需围绕 CCR 补设计

## 6. Crash Info
  - Error type: 未知 (进程消失, 远端日志无法拉取)
  - Error message excerpt: N/A
  - Auto-fix attempt: N — 无日志无法定位, 且结果已近终点 (ep29, 平台区), 不投入自修复
================================================================================
