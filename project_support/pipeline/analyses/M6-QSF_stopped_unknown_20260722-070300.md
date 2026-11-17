================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M6-QSF | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M6-QSF
  - Config: configs/Quard/qsf/model_base1_quard2_c2f_enc_lite_posA_l1_qsf.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-07-21 ~16:03 | Finished: 2026-07-22 ~03:00 (process disappeared)
  - Duration: ~11h | Epochs: ~30/50
  - State: stopped_unknown

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4866 | 30      |
  | Acc@50   | N/A    | N/A     |
  | spmIOU   | N/A    | N/A     |
  (Note: remote log unavailable, checkpoint left on server-4)

## 3. Convergence Summary
  - Best first reached at: epoch ~22 (0.4866)
  - Subsequent no_improve epochs: ~8 (epochs 23-30 unchanged at 0.4866)
  - Progression: 0.3605(ep3) → 0.4808(ep12) → 0.4844(ep14) → 0.4848(ep15) → 0.4866(ep22) → plateau 0.4866(ep23-30)
  - 收敛形态: 前期单调上升 → ep22 后平台，近 8 epoch 无任何提升

## 4. Comparison
  - vs baseline (model_base1, 0.4894): γ = -0.0028 (失败)
  - vs champion (posA_l1, 0.5012): γ = -0.0146 (大幅落后)
  - vs M1-QGC (query-gated context, 0.4939): γ = -0.0073 (差于 query gate 方案)
  - M6-QSF 机制: query 进尺度融合 gate（用 instance query 调制 3 尺度 cluster token 融合权重）
  - 结论: query-selective fusion gate 未带来提升，反比 M1 简单 gate 更差

## 5. Conclusion
  - 结论: [失败] — QSF (Query-Selective Fusion gate) 无效
  - 解释: 用 instance query 动态调制多尺度融合权重的 gate 机制，最终 mIoU=0.4866 < baseline 0.4894，不仅无收益还降点。对比 M1-QGC (query-gated context, 简单 gate 不加到融合中) 也低了 0.0073，说明 query 进融合 gate 引入额外复杂度无益。
  - 对后续实验设计的建议: 放弃 query-selective fusion 方向。M18/M19 的 2-scale 消融（去掉一个尺度而非增加 gate）是正确的追问方向——直接消融尺度数对性能的贡献。

## 6. Crash Info (if crashed)
  - Error type: stopped_unknown (进程消失，非正常退出)
  - Error message excerpt: 远程进程在 ep30 后消失，日志拉取失败（checkpoint 留在远端 /data/songcl/Project/Cluster_project/Cluster_checkpoints/server_4/...）
  - Auto-fix attempt: N — stopped_unknown 属进程异常退出，非代码 bug；后续 M17-ORT 已入替 GPU0
================================================================================
