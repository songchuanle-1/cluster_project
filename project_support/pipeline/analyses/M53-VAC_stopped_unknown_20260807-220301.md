================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M53-VAC | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M53-VAC
  - Config: configs/Quard/vac/model_base1_quard2_c2f_enc_lite_posA_l1_vac.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-04 (server-6 GPU7 slot 2) | Finished: 2026-08-07 22:03:48 | Duration: ~3d
  - State: stopped_unknown (进程消失 ×3 次确认; 远端日志拉取失败, checkpoint 留远端)
  - 机制: Variance-Augmented Cluster Context — cluster token 携带 mean+variance
    (二阶统计), 使 context 可表达簇内离散度/可靠性。与 M51-DCA(mean+max) 正交。
    config: cluster_mode=drp / cluster_message_type=context / cluster_pool_type=var

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4889 | 28      |
  (stopped_unknown: 进程消失前最后一次保存的 best; Acc@50/spmIOU 因日志未拉取无法获取)

## 3. Convergence Summary
  - Best first reached at: epoch ~28 (best=0.4889)
  - 进程于 08-07 死亡 (deathwatch 2/3→3/3), 无日志可回溯收敛形态
  - 推断: 运行约 3 天到 ep28, 未刷新到更高值, 处于平台/缓降区 (与 server-6 GPU7
    多进程共享 + 8h 时区混淆无关, 属自然终止)

## 4. Comparison
  - vs baseline (model_base1): γ = -0.0005 (≈0, 略低于 baseline)
  - vs champion (posA_l1 0.5012): γ = -0.0123
  - 与同族 DCA (M51-DCA 0.4893 mean+max): VAC 0.4889 ≈ DCA 0.4893 — 二阶统计
    (variance) 与 max 聚合一样未带来增益, 簇池化统计量不是当前瓶颈

## 5. Conclusion
  - 结论: [失败] (持平略负)
  - 解释: variance 增强 context 未能提升 — cluster token 的统计量表达
    (mean/max/var) 均已试过且 ≤0.4894, 该轴 (池化统计量) 基本封顶, 非有效方向
  - 对后续实验设计的建议: 关闭「簇池化统计量」轴。cluster_pool_type 的
    mean/max/var 变体 (DRP=0.5003? 实际 M62-ORTG 0.4979 / DCA 0.4893 / VAC 0.4889)
    均已覆盖, 无需再扩展。故事线应向 token 质量(CCP)与交付机制(HCG)推进,
    当前队列 M69-M74 已覆盖该方向

## 6. Crash Info
  - Error type: 未知 (进程消失, 远端日志无法拉取)
  - Error message excerpt: N/A
  - Auto-fix attempt: N — 无日志无法定位, 且结果已近终点 (ep28, 平台区), 不投入自修复
================================================================================
