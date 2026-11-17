================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M55-SCF | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M55-SCF
  - Config: configs/Quard/scf/model_base1_quard2_c2f_enc_lite_posA_l1_scf.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-04 20:58:00 | Finished: 2026-08-05 11:17:33 | Duration: ~14.3h
  - State: done_earlystop (训练脚本自身 early-stop, 非 pipeline 干预)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4927 | ~25/50  |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (末次验证 0.4803@ep25, 触发 no_improve=10/10 早停, best=0.4927)

## 3. Convergence Summary
  - Best first reached at: epoch <25 (监控曲线 10/50=0.4750 → 25/50=0.4927, 持续上升后平台)
  - Subsequent no_improve epochs: 10/10 (训练脚本在 ep25 触发早停)
  - Final epoch best: mIoU=0.4927 (25/50) vs 末次验证 0.4803 — 收敛形态: 上升后平台期,
    未刷到 champion 级别即触发 patience

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0033 (有效, 但低于 champion)
  - vs current champion (DRP 0.5012): γ = -0.0085 (失败)
  - 融合机制轴对照: SWI(静态gate)=0.4970 / CSF(内容注意力)=0.4958 / SCF(内容自适应)=0.4927
    — 三者均 < champion 0.5012, 融合权重形式非瓶颈

## 5. Conclusion
  - 结论: [失败]
  - 解释: Scale-Content Fusion (内容自适应融合权重, 权重感知各尺度 token 内容) 0.4927
    显著低于 champion 的静态 [point_feats, global_mean] gate (0.5012), 融合机制轴收束 —
    让 gate 感知尺度 token 内容无益, 静态 per-point gate 已够用。
  - 对后续实验设计的建议: 融合机制方向不再扩展 (SWI/CSF/SCF 全 < champion);
    瓶颈不在此处。新设计应转向 readback 的**尺度交付**结构 (详见 12:08 motivation_review
    — 粗尺度 gather 长度错配, 多数点收不到粗尺度 context)。

## 6. Crash Info (if crashed)
  - 无 crash — 训练脚本正常 early-stop 退出, 进程随后从 GPU0 释放, deathwatch 计数因
    进程消失而累加, 本 tick 已按终态归档并从 deathwatch/running.json 移除。
================================================================================
