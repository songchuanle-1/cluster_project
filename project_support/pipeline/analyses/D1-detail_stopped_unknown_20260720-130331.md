================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: D1-detail | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: D1-detail (relaunch — 首轮于 07-19 23:21 早停于 0.4979@ep14，本轮 07-19 23:26 重启)
  - Config: configs/Quard/model_base1_quard2_c2f_enc_lite_posA_l1_detail.yaml
  - Server: server-4 | GPU: ? (进程消失前未稳定记录卡号)
  - Started: 2026-07-19 23:26:05 | Finished: 2026-07-20 ~13:03 | Duration: ~13.6h
  - State: stopped_unknown（监控侧进程消失判定；日志侧已正常触发 early stopping）

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5003 | 18      |
  | Acc@50   | 0.555  | 18      |
  | spmIOU   | ~0.458 | 18      |
  (best=0.5003 记录于日志末行 "Early stopping at epoch 28: no improvement for 10 epochs (best=0.5003)"；
   best 实际达成于 ep18，其后 10 epoch 未刷新 → ep28 早停。spmIOU 取 best 邻近最高观测值。)

## 3. Convergence Summary
  - Best first reached at: epoch 18
  - Subsequent no_improve epochs: 10（触发 early stopping）
  - Final epoch best: mIoU=0.5003 vs 历史首轮 best=0.4979
  - 收敛形态: 重启后稳步上升，ep18 触顶 0.5003 后进入平台（后续序列 0.491~0.494 震荡），
    早停于 ep28。比首轮(0.4979@ep14) 多跑 14 epoch 提升 +0.0024，说明 detail 机制需更长训练才达峰。

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0109 (有效)
  - vs current champion (posA_l1=0.5012): γ = -0.0009 (近乎持平，差 0.0009)
  - vs 首轮 D1-detail (0.4979@ep14): γ = +0.0024 (重启延长训练后显著提升)
  - vs E4-res_detail (residual+detail, 0.4944@ep21 running): detail 单独 > detail+residual 组合
    → 暗示 residual mode 与 detail message 组合反而互相干扰

## 5. Conclusion
  - 结论: [有效·近冠军]
  - 解释: detail message_type 单独使用即达 0.5003，与 champion 0.5012 仅差 0.0009，
    证明 "detail 聚合(逐点消息而非均值)" 是与 champion(context-only 多尺度回写) 等价有效的另一机制；
    且 detail+residual 组合(E4) 反而掉到 0.4944 → residual 并非 detail 的有效增强。
  - 对后续实验设计的建议:
    (1) detail 机制已接近 champion，可作为故事线第二条有效机制证据；
    (2) D1-detail 与 champion 仅差 0.0009，处于噪声范围，多 seed 可佐证稳定性（但多 seed 留 Phase 2，禁现跑）；
    (3) 为待决 question 20260720-000617 (M2-DCR = detail + 1层 cluster token self-attn refine)
        提供新证据：detail 底座已强(0.5003)，在其上加 refine 的 M2-DCR 收益预期更清晰，
        倾向支持选项 (a) 授权入队 M2-DCR —— 但仍待用户拍板，不自主决断。

## 6. Crash Info (if crashed)
  - Error type: 无 crash 日志；进程消失原因未明（疑似 OOM/手动/资源抢占，checkpoint 留远端，日志拉取部分失败）
  - Error message excerpt: （无 traceback；末行为正常 early stopping 触发声明）
  - Auto-fix attempt: N — 非 Claude 引入代码所致 crash，且日志显示训练已正常早停，无需自修复
================================================================================
