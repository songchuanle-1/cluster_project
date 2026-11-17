================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: D1-detail | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: D1-detail
  - Config: configs/Quard/model_base1_quard2_c2f_enc_lite_posA_l1_detail.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-07-19T10:16 | Finished: 2026-07-19T23:02 | Duration: ~13h
  - State: stopped_unknown (ep14 中途断开, 疑并发 tick sync/git clean 干扰; 非自然早停)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4975 | ~14     |
  | Acc@50   | 0.551  | ~14     |
  | spmIOU   | 0.462  | ~14     |
  (末次 save best: mIOU 0.497 / Acc_50 0.551 / spmIOU 0.462; 仍单调上升未刷顶)

## 3. Convergence Summary
  - Best first reached at: epoch ~14 (0.4975, 末次记录)
  - Subsequent no_improve epochs: 0 (被中断时尚在上升)
  - 验证序列: 0.474 → 0.484 → 0.485 → 0.493 → 0.496 → 0.497 (ep9~14, 单调上升无平台)
  - 收敛形态: 持续单调上升, 未见平台/回落 — 未收敛即被中断, 当前 0.4975 非真实上限

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0081 (有效, 三候选中最强)
  - vs champion (PosA_l1=0.5012): γ = -0.0037 (未超越, 但仍在上升)
  - vs B5-residual (0.4944): γ = +0.0031
  - vs C3-refine (0.4931): γ = +0.0044
  - D1 是机制三候选 (B5/C3/D1) 中 best 最高且唯一未收敛者

## 5. Conclusion
  - 结论: [有效·最有潜力] — cluster_message_type=detail (独立点-簇归一化残差) +0.0081 vs baseline, 三候选最强
  - 解释: detail 消息类型 (点-簇独立归一化残差) 比 residual(0.4944)/refine(0.4931) 更贴合 "聚类矩阵→点云特征" 动机; 单调上升说明信号未饱和, 真实上限高于 0.4975
  - 对后续实验设计的建议: D1 被意外中断, 须重跑到自然终态 (done_complete/done_earlystop) 才能定论; 重跑优先级 P0。重跑后若仍单调上升, 考虑延长 epochs / 与 residual 组合 (E4-res_detail 已在跑, 可交叉验证 detail 的独立贡献)
  - 注意: 当前 0.4975 受中断污染, 不得作为 detail 方向的最终结论

## 6. Crash Info (if crashed)
  - Error type: stopped_unknown (非 CUDA OOM / 非维度错误; 进程消失但无 traceback)
  - Error message excerpt: 日志末位为 ep14 训练进度条, 无异常栈; PID 文件标记 DEAD
  - 根因推测: 并发 tick 的 sync/git clean 误清运行时文件, 或外部 kill
  - Auto-fix attempt: N — 非代码 crash, 无需 bugfix; 处置为重跑 (见 §5)
================================================================================
