================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: F1-2layer | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: F1-2layer
  - Config: configs/Quard/2layer/model_base1_quard2_c2f_enc_lite_posA_l1_2layer.yaml
  - Model: model_base1_quard2_c2f_enc_lite_posA_l1_2layer (独立包, 复制自 champion)
  - Server: server-4 | GPU: 1
  - Started: 2026-07-19T23:03 | Finished: 2026-07-19T23:09 | Duration: ~6min
  - State: stopped_unknown (ep1 iter 410 被手动 kill 让位 D1 resume)

## 2. Best Metrics
  | Metric | Value | @ Epoch |
  |--------|-------|---------|
  | mIoU   | —     | 无验证  |
  (ep1 未完成, 无 Validation)

## 3. Convergence Summary
  - 仅跑到 ep1 iter 410/4686, 无任何验证指标
  - 无收敛信息

## 4. Comparison
  - 无法对比 (无指标)

## 5. Conclusion
  - 结论: [未完成·无数据] — 2层 cluster_attn 假设未验证
  - 解释: 为恢复 D1-detail (更有潜力, 0.4975上升中) 主动让位 kill
  - 对后续实验设计的建议: D1/E4 出结果后, 若 detail 方向有效, 重跑 F1 (2层 attn) 作为超参消融

## 6. Crash Info
  - 无 crash, 手动 kill 让位
  - 无 checkpoint (ep1 未存)
================================================================================
