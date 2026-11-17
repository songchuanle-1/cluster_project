================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M56-DOT | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M56-DOT
  - Config: configs/Quard/dot/model_base1_quard2_c2f_enc_lite_posA_l1_dot.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-04 18:03:39 | Finished: 2026-08-04 20:03:30 | Duration: ~2h
  - State: stopped_unknown (进程消失 ×3 次确认; 实际进程 ~18:33 本地时间死亡)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | — (无验证产出) | — |
  | Acc@50   | —       | — |
  | spmIOU   | —       | — |
  (日志显示训练至 epoch1 iter 20/4686 后无 traceback 静默死亡, 无任何验证结果)

## 3. Convergence Summary
  - 无收敛数据。远程日志 train_..._dot_20260804_180321.log 显示模型加载完成、profile
    阶段结束、开始 Train[1/50], iter_time~14s (GPU7 与 M52/M53/M54 共享, 严重减速),
    20 iters 后日志中断, 无 Error/Traceback/Killed 记录。
  - 形态: 训练刚起步即被杀, 属资源层 kill 而非代码错误。

## 4. Comparison
  - vs baseline (0.4894): 无结果可比。
  - vs champion DRP (0.5012): 无结果可比。
  - 与 M57-DET-ORT 同批死亡; 与 M17-ORT 同受 ORT 梯度断流 bug 污染。

## 5. Conclusion
  - 结论: [失败] (无效实验 — 无 mIoU 产出)
  - 解释: M56-DOT 是 DRP+ORT 组合 (cluster_mode=drp_ort), 但存在双重失效: ① dec.py 的
    reset/get_orth_loss 仅匹配 == 'ort', 漏掉 'drp_ort', 故 orth 正则从未被收集;
    ② 即使收集, hier_postprocess 的 .detach().item() 也使 orth 梯度恒为 0。因此 M56 结果
    等价于纯 DRP, 且进程因 GPU7 过载 (3 任务已满 + M56 + M57 = 5 任务) 死亡。
  - 对后续实验设计的建议: 该假说由 M62-ORTG (修复梯度断流后) 重测; server-6 GPU7 不可再
    叠加超过 max_tasks_per_gpu=3 的任务。

## 6. Crash Info (if crashed)
  - Error type: 进程静默死亡 (无 traceback), 判定为资源层 kill
  - Error message excerpt: 无错误日志; 最后一行 `Train[1/50]: 20/4686 [04:41<..., iter_time=14.05]`
  - Auto-fix attempt: N — 实验代码本身已由 M62-ORTG 替代修复
================================================================================
