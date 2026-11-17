================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: E4-res_detail | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: E4-res_detail
  - Config: configs/Quard/residual_detail/model_base1_quard2_c2f_enc_lite_posA_l1_residual.yaml
  - Server: server-4 | GPU: ? (进程消失前未稳定记录卡号)
  - Started: ~2026-07-20 00:xx | Finished: ~2026-07-20 16:03 | Duration: ~15h
  - State: stopped_unknown（监控侧进程消失判定；远程无 train.log / stderr.log / checkpoints 残留）

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4944 | 21      |
  | Acc@50   | ~0.549 | 21      |
  | spmIOU   | ~0.453 | 21      |
  (来源: pipeline_monitor 上报 + experiments.csv 末行; spmIOU/Acc@50 为近似值，因日志已清理)

## 3. Convergence Summary
  - Best first reached at: epoch ~21
  - Subsequent no_improve epochs: 未确定（进程消失，无法判断是否为正常早停）
  - Final epoch best: mIoU=0.4944 vs D1-detail(单独)=0.5003
  - 收敛形态: 早期稳步上升（ep8=0.4584 → ep15≈0.49 → ep21=0.4944），ep21 后进入平台。
    与 D1-detail(0.5003@ep18) 相比，residual 叠加 detail 反而使 best 低 0.006，且收敛更慢。

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0050 (边际有效)
  - vs current champion (posA_l1=0.5012): γ = -0.0068 (失败)
  - vs D1-detail (单独=0.5003): γ = -0.0059 (residual 叠加 detail 反而掉点)
  - vs B5-residual (单独=0.4944): γ ≈ 0 (持平 — B5 也是 0.4944)
    → residual 无论单独还是与 detail 组合，效果相同（~0.4944），说明 residual 机制
      上限固定，detail 叠加无协同效应

## 5. Conclusion
  - 结论: [失败·组合无协同]
  - 解释: residual 模式(message_type=residual) 与 detail 模式组合后未产生协同，
    反而互相干扰: E4=0.4944 < D1-detail=0.5003。residual 机制的上限似乎在 ~0.4944
    (B5 单独也是此值)，无法被 detail 消息类型突破。
  - 对后续实验设计的建议:
    (1) residual 路线可正式放弃（banned 扩展: residual 系 + residual+detail 组合）;
    (2) detail 机制独立有效(0.5003)，后续在 detail 底座上叠加其他机制(如 M2-DCR)
        仍值得探索;
    (3) 本实验因进程消失无完整日志，但 metrics 序列已足够支撑结论。

## 6. Crash Info (if crashed)
  - Error type: 进程消失（stopped_unknown），无 crash traceback
  - Error message excerpt: 远程 /data/songcl/.../tools/train/ 下无该实验目录残留;
    /data/songcl/.../Checkpoints/ 下无对应 checkpoint
  - Auto-fix attempt: N — 非 Claude 引入代码所致（residual_detail 包已存在且之前正常训练过）;
    进程消失原因推测为 OOM/资源抢占/手动 kill
================================================================================
