================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: D1-detail | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: D1-detail
  - Config: configs/Quard/model_base1_quard2_c2f_enc_lite_posA_l1_detail.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-07-19T10:16 | Finished: 2026-07-19T23:02 | Duration: ~13h
  - State: stopped_unknown (ep14 中途断开, 非正常终态)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4975 | 14      |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch 14 (0.4975, 最新一次 val)
  - 序列: 0.4617→0.4737→0.4845→0.4853→0.4927→**0.4975** 持续单调上升
  - 断点: ep14 iter 3620/4686 中途停止, 无 crash traceback, 无 Validation 完成
  - 收敛形态: 强势单调上升, 未现平台, **潜力未充分释放**

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0081 (有效)
  - vs champion (PosA_l1=0.5012): γ = -0.0037 (未超越, 但仍在上升)
  - vs B5-residual (0.4944): γ = +0.0031
  - vs C3-refine (0.4931): γ = +0.0044
  - vs C1-layerscale (0.4998): γ = -0.0023 (接近)

## 5. Conclusion
  - 结论: [有效·未完成] — detail message_type 是本批最有潜力方向
  - 解释: 0.4617→0.4975 单调上升无平台, ep14 仍刷新 best。若跑完可能逼近或超 champion 0.5012
  - 对后续实验设计的建议: **D1 应重跑完成**; E4 (residual+detail) 组合基于此方向, 优先级提升

## 6. Crash Info
  - Error type: 无 crash 日志, 进程中途消失
  - 推测根因: 并发 headless tick 的 sync.sh `git clean` 干扰远端 logs/ 写入句柄 (与 B5 note 同类问题)
  - Auto-fix attempt: N — 非代码 crash
================================================================================
