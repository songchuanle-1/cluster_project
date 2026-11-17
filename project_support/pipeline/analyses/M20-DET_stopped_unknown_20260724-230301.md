================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M20-DET | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M20-DET
  - Config: configs/Quard/model_base1_quard2_c2f_enc_lite_posA_l1_detail.yaml
  - Server: server-4 | GPU: 1
  - Started: ~2026-07-24 06:07 | Finished: 2026-07-24 ~22:00 | Duration: ~16h
  - State: stopped_unknown (进程消失，非正常退出)
  - Label: D1-detail clean rerun #3 — detail message_type (逐点 detail 特征回写) on top of champion

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4955 | 23      |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (日志留远端无法拉取，仅凭 pipeline_monitor 探测值)

## 3. Convergence Summary
  - Best first reached at: epoch ~23 (0.4955)
  - Subsequent no_improve epochs: 9/10 (即将触发早停前进程消失)
  - 序列不可得 (日志远端不可读)
  - 收敛推断: 第三轮 detail 训练始终低于前两轮 (0.4979/0.5003)，约在 0.49 附近平台

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0061 (有效，但弱于 champion)
  - vs champion (posA_l1 0.5012): γ = -0.0057 (未超越)
  - vs D1-detail run1 (0.4979): γ = -0.0024
  - vs D1-detail run2 (0.5003): γ = -0.0048
  - 三轮 detail 变体趋势: 0.4979 → 0.5003 → 0.4955，波动大，无稳定提升

## 5. Conclusion
  - 结论: [持平/轻微有效]
  - 解释: detail message_type 三轮最佳 0.5003 (距 champion 仅 0.0009)，但三轮波动大 (0.4955~0.5003)，说明 detail 独立有效但上限约在 0.500 附近，无法稳定超越 champion context-only (0.5012)
  - 对后续实验设计的建议: detail 方向上限已探明 — 单独 detail 约 0.500，与 champion 差距 <0.001 但在统计噪声范围内。等 M21-HYB (context+detail hybrid) 和 M24-ORT-D (ORT+detail) 出结果后可判断组合是否有增益。不建议再单独跑 detail 变体

## 6. Crash Info (if crashed)
  - Error type: stopped_unknown (进程消失，非 crash)
  - Error message excerpt: N/A — pipeline_monitor 探测到 queue 中 running 但进程不在 ps aux 中
  - Auto-fix attempt: N/A — 非代码 crash，无需修复。队列已自动替换
================================================================================
