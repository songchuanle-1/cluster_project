================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M136-MLAY-DCMV | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M136-MLAY-DCMV
  - Config: configs/Quard/mlay_dcmv/model_base1_quard2_c2f_enc_lite_posA_l1_mlay_dcmv.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-26 01:10 (queue_push, 承接 M134-DUAL 早停释放的 gpu0) | Finished: 2026-08-26 13:07
  - Duration: ~11.9h
  - State: done_earlystop (no_improve=11/10, monitor kill PID=1884963)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4960 | 21/50   |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (日志拉取失败, checkpoint 留远端; 指标来源 pipeline_monitor 日志尾解析)
  monitor 近5次验证序列: 0.4530, 0.4910, 0.4520, 0.4940, 0.4560 — Best 后震荡

## 3. Convergence Summary
  - Best first reached at: epoch 21 (mIoU=0.4960)
  - Subsequent no_improve epochs: 11/10 (monitor kill)
  - Final epoch best: mIoU=0.4960 (21/50)
  - 收敛形态: 前 10 ep 快速上升后高位震荡 (0.49-0.496 平台), 未再创新高

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = +0.0066 (有效)
  - vs current champion (M95-CTF-HCG-CSORT = 0.5020): γ = -0.0060
  - vs M126-MLAY-DCM (多层×DCM, 0.4980): γ = -0.0020 — {多层 legacy}×{DCMV} 低于 ×{DCM}
  - vs M133-DCMV (qia 单通路, 0.4950): γ = +0.0010 — 多层注入对 DCMV 几乎无增益
  - vs M125-MLAY-DCA (多层×DCA, 0.4970): γ = -0.0010

## 5. Conclusion
  - 结论: [失败/不叠加] — M136 = {MLay 2层 legacy}×{DCMV} = 0.4960, 与通路组合
    全不叠加的既有结论一致 (M125/M126/M134)
  - 解释: DCMV (qia 视觉通路) 单通路上限 ~0.495 (M133), 叠加多层注入 (M136=0.4960)
    仅 +0.001, 与 M125/M126 (多层×decoder-access 不叠加) 同形态 — 多层注入与
    decoder-access 两条有效轴在组合时无协同。DCMV 通路本身已确认弱 (M134 矩阵
    补格时 qia=0.4950)。
  - 对后续实验设计的建议: ① 多层×decoder-access 组合轴确认关闭, 不再设计
    该 2×2 剩余格; ② token 信息量两条 loss 路径 (M140-CLICA / M141-CSIC) 是
    当前唯一未证伪假设, 本轮设计 M142 (双监督 combo) 补 {判别性}×{一致性} 组合格;
    ③ seed 对照 (M122/M137) 继续确认机制 vs seed-1999 归属。

## 6. Crash Info
  - Error type: N/A (早停 kill, 非 crash)
  - Auto-fix attempt: N
================================================================================
