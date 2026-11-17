================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M50-DGC | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M50-DGC
  - Config: configs/Quard/dgc/model_base1_quard2_c2f_enc_lite_posA_l1_dgc.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-04 04:03:19 | Finished: 2026-08-04 ~20:31 (进程消失, deathwatch 确认)
  - Duration: ~16.5h
  - State: stopped_unknown (进程消失 ×3 次确认, 27/50 时死亡)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4913 | 27      |
  | Acc@50   | 0.544  | ~27     |
  | spmIOU   | 0.456  | ~27     |
  (来源: experiments.csv + 远程日志 mIOU 序列; 日志最终 mIOU≈0.482, 低于 best)

## 3. Convergence Summary
  - Best first reached at: epoch ~27 (0.491)
  - 之后序列: 0.489, 0.489, 0.486, 0.488, 0.485, 0.486, 0.477, 0.483, 0.480, 0.482
    → best 后 9 个 epoch 未刷新, 平台缓慢下行
  - 形态: 快速上升至 0.491@ep27, 之后 0.48-0.49 区间震荡下行, 已满足早停条件但进程先死亡

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0019 (微弱有效, context 收益保留)
  - vs champion (posA_l1/DRP 0.5012): γ = -0.0099 (失败, 未破 ceiling)
  - vs M49-NLR (0.4948): γ = -0.0035 (DGC < NLR)
  - vs M48-BIL (0.4919): γ = -0.0006 (DGC ≈ BIL)

## 5. Conclusion
  - 结论: [失败] — difference-gated context 未带来增益
  - 解释: DGC 用 difference gate 控制 context 读回强度, 0.4913 仍低于 champion 0.5012。
    与 BIL(0.4919)/NLR(0.4948) 串联: 读回形式轴进一步确认 — 简单加法 readback
    (champion 的 feat += gate*msg) 仍是最优, gate 的差分形式无独立收益。
  - 对后续实验设计的建议: 读回 expressiveness 轴 (BIL/NLR/FILM/FLM/DGC) 完全闭合。
    剩余未测的 message 构造空白是 per-scale 残差 (M63-PSR, 已入队) — 方向从
    "读回形式" 转向 "message 构造" (绝对 vs 残差 vs 逐尺度残差)。

## 6. Crash Info (if crashed)
  - Error type: 进程静默死亡 (无 traceback; 日志最后为 epoch 22 训练进度条后中断)
  - Error message excerpt: 无 Error/Traceback/Killed 记录 — 资源层 kill 或环境问题
  - Auto-fix attempt: N — 非本 tick 引入的 crash; deathwatch 3 次确认后判定 stopped_unknown
================================================================================
