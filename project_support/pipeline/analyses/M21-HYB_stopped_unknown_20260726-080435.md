================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M21-HYB | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M21-HYB
  - Config: configs/Quard/model_base1_quard2_c2f_enc_lite_posA_l1_hy.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-07-24 06:07 | Finished: 2026-07-26 08:03 | Duration: ~50h
  - State: stopped_unknown (process disappeared, no crash traceback)
  - Label: M21 Hybrid context+detail message: hybrid message_type combining context and detail pathways

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4898 | 25      |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (from pipeline_monitor: Best=0.4898 @ epoch 25/50)

## 3. Convergence Summary
  - Best first reached at: epoch 25 (0.4898)
  - Subsequent no_improve epochs: unknown (process disappeared)
  - Final epoch best: mIoU=0.4898
  - 收敛形态: 缓慢上升至ep25峰值(0.4898), 未达到champion水平, 过程无显著突破
  - 序列: 0.4652, 0.4638, 0.4685, 0.4795, 0.4770 (monitor visible range)

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0004 (持平, 几乎无增益)
  - vs champion (posA_l1=0.5012): γ = -0.0114 (显著劣于champion)
  - vs context-only (champion 0.5012): γ = -0.0114
  - vs detail-only (D1-detail 0.5003): γ = -0.0105
  - vs ORT (M17-ORT 0.5005): γ = -0.0107
  - Hybrid context+detail message_type 不仅未产生协同增益, 反而消解了两者的独立收益

## 5. Conclusion
  - 结论: [失败] — hybrid message_type (context+detail组合) 无效, mIoU几乎等于baseline
  - 解释: 同时使用 context(按cluster ID回写聚合特征)和 detail(点-簇归一化残差)两种消息类型,
    二者信息冲突/冗余导致性能退化至baseline水平。context-only(champion 0.5012)和detail-only(0.5003)
    分别有效, 但组合无协同且相互抵消。类似 E4-residual+detail(0.4944)的组合失败模式。
  - 对后续实验设计的建议: 放弃 hybrid message_type 方向。组合实验应聚焦 ORT+detail(M24-ORT-D running)
    和 ORT+refine 等不同维度机制的组合, 避开同维度(message_type)的组合。
================================================================================
