================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M121-CTF-HCG-MLAY-DET | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M121-CTF-HCG-MLAY-DET
  - Config: configs/Quard/det_mlay/model_base1_quard2_c2f_enc_lite_posA_l1_det_mlay.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-20 18:37:50 | Finished: 2026-08-28 08:07:33 | Duration: ~183h
    (含 08-21/08-22 GPU7 3任务超容量争抢期, 单任务速率受扰)
  - State: done_earlystop (no_improve=11/10, monitor kill PID=4040343)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4950 | 18/50   |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (Acc50/spmIOU 缺失: monitor 未记录, 日志留远端; 验证序列: 0.4610, 0.4940, 0.4580, 0.4940, 0.4560)

## 3. Convergence Summary
  - Best first reached at: epoch 18 (mIoU=0.4950)
  - Subsequent no_improve epochs: 11 (early-stopped, patience=10)
  - Final epoch best: mIoU=0.4950 vs historical best=0.4950
  - 收敛形态: 缓慢爬升 (受 GPU7 资源争抢速率拖慢), ep18 达 0.4950 后平台
    震荡 (0.456-0.494), 未刷新

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0056 (有效)
  - vs current champion (M95-CTF-HCG-CSORT=0.5020): γ = -0.0070
  - vs M86-MLAY (legacy 2层单独=0.5010): γ = -0.0060
  - vs D1-detail (0.5003): γ = -0.0053
  - vs M126-MLAY-DCM (0.4980) / M138-MLAY-DUAL (0.4990): 同形态 — MLay×delivery 组合不叠加

## 5. Conclusion
  - 结论: [失败] — {MLay 2层 legacy}×{detail 残差 message} 组合 0.4950,
        低于两个单独机制 (MLay=0.5010, detail=0.5003), 不叠加
  - 解释: MLay (2层注入) 与 detail (残差 message 构造) 均属 delivery 结构机制,
    信息流在 writeback 通道重叠, 无正交增益 — 与 M125/M126/M134/M136/M138/M139
    模式一致, 是 delivery×delivery 组合轴第 7 次确认不叠加。
  - 对后续实验设计的建议: MLay×delivery 组合格正式关闭。delivery×delivery 轴
    已 7 次失败, 不再投入。开放方向收敛为: CSORT 系跨类组合 (M145/146/147/148,
    {正则化}×{delivery}) 与 loss 监督轴 (M142/143/144) — 若这批也全不破
    0.5020 → 范式级 question, 暂停自主设计。

## 6. Crash Info (if crashed)
  - N/A (早停正常, 无 crash; 曾因 GPU7 超容量受扰但未崩溃)
================================================================================
