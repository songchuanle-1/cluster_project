================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M57-DET-ORT | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M57-DET-ORT
  - Config: configs/Quard/det_ort/model_base1_quard2_c2f_enc_lite_posA_l1_det_ort.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-04 18:26:24 | Finished: 2026-08-04 20:03:32 | Duration: ~1.5h
  - State: stopped_unknown (进程消失 ×3 次确认)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | — (无验证产出) | — |
  | Acc@50   | —       | — |
  | spmIOU   | —       | — |
  (远程日志 train_..._det_ort_20260804_182606.log 显示 profile 阶段后 Train[1/50] 起步,
  进程静默死亡, 无验证结果)

## 3. Convergence Summary
  - 无收敛数据。训练起步于 GPU7 已满载 3 任务 + M56 的情况下 (第 5 个进程), 日志中断于
    Train[1/50] 早期, 无 traceback。

## 4. Comparison
  - vs baseline (0.4894): 无结果可比。
  - vs champion DRP (0.5012): 无结果可比。
  - 与 M56-DOT 同批死亡; ORT+detail 组合假说未经验证。

## 5. Conclusion
  - 结论: [失败] (无效实验 — 无 mIoU 产出)
  - 解释: M57-DET-ORT 是 ORT + detail message_type 组合。同样受 ORT 梯度断流 bug 影响
    (detail 包源自 ort 系), 且进程因 GPU7 过载死亡。该变体同时叠加了两个未验证组件
    (detail 与 ORT), 即使跑完也难归因, 属低优先级设计。
  - 对后续实验设计的建议: detail 单独收益已由 D1-detail (0.5003) 确认; ORT 部分由 M62-ORTG
    重测。M57 组合方案不再重跑。

## 6. Crash Info (if crashed)
  - Error type: 进程静默死亡 (无 traceback), 判定为资源层 kill
  - Error message excerpt: 无错误日志; 最后内容为 profile 的 Unsupported operator 警告
  - Auto-fix attempt: N — 实验已被 M62-ORTG 取代
================================================================================
