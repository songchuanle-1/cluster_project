================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M141-CTF-HCG-CSIC | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M141-CTF-HCG-CSIC
  - Config: configs/Quard/ctf_hcg_csic/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csic.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-27 17:09 | Finished: 2026-08-28 06:07 | Duration: ~13h
  - State: done_earlystop (no_improve=11/10, monitor kill PID=3971094)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4960 | 23/50   |
  | Acc@50   | 0.548  | 23      |
  | spmIOU   | 0.459  | 23      |

## 3. Convergence Summary
  - Best first reached at: epoch 23 (mIoU=0.496)
  - Subsequent no_improve epochs: 11 (early-stopped, patience=10)
  - Final epoch best: mIoU=0.496 vs historical best=0.496
  - 收敛形态: 快速上升至 0.493@ep14 后震荡平台 (0.488~0.496), 未突破 0.497

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0066 (有效)
  - vs current champion (M95-CTF-HCG-CSORT=0.5020): γ = -0.0060
  - vs 同轴 M140-CLICA (0.4970): γ = -0.0010
  - vs 父模型 M81-CTF-HCG (0.5012): γ = -0.0052

## 5. Conclusion
  - 结论: [失败] — CSIC (跨尺度实例一致 loss) 未破平台, 与 CLICA 同形态
  - 解释: cluster token 跨尺度一致性监督 (0.4960) 与同尺度判别监督 (0.4970)
    均低于父模型 0.5012 — loss 监督轴第二点证伪, 直接监督 cluster token
    语义不能带来 >0.001 增益。
  - 对后续实验设计的建议: loss 监督轴已两点失败 (CLICA=0.4970 / CSIC=0.4960)。
    M142 (双监督) 与 M143 (OBJG) 仍在跑/排队, 若也 ≤0.502 → 该轴关闭,
    平台突破只能靠结构机制 (CSORT 系 / MLay 系)。

## 6. Crash Info (if crashed)
  - N/A (早停正常, 无 crash)
================================================================================
