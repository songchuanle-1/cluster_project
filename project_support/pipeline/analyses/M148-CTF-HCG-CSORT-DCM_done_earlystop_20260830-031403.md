================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M148-CTF-HCG-CSORT-DCM | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M148-CTF-HCG-CSORT-DCM
  - Config: configs/Quard/ctf_hcg_csort_dcm/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_dcm.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-29 14:09 | Finished: 2026-08-30 03:07 | Duration: ~13.0h
  - State: done_earlystop (no_improve=11/10, monitor kill PID=1774462)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4990 | 19/50   |
  | Acc@50   | 0.551  | 19      |
  | spmIOU   | 0.464  | 19      |

## 3. Convergence Summary
  - Best first reached at: epoch 19
  - Subsequent no_improve epochs: 11 (early-stopped by monitor, patience=10)
  - Final epoch best: mIoU=0.4990 vs historical best=0.4990
  - 收敛形态: 快速上升至 ep19 峰值 0.499 后平台回落 (0.492/0.488/0.495/0.495), 未再刷新

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0096 (有效)
  - vs champion (M95-CTF-HCG-CSORT 0.5020): γ = -0.0030 (未破顶)
  - vs M124-CTF-HCG-DCM alone (0.5010): CSORT×DCM = 0.4990 < DCM alone 0.5010
    → 负交互 (组合不叠加第 N 例)
  - vs M146-CSORT-DET (0.4970, message-type 轴关闭): +0.0020, DCM 优于 DET 但同样不叠加

## 5. Conclusion
  - 结论: [失败] (对 champion 而言)
  - 解释: CSORT (0.5020) × DCM decoder-access (0.5010) 组合 = 0.4990, 低于两个父
    机制 — 再次印证"组合不叠加"规律。decoder-access 轴 (用户 08-10 批准突破方向①
    之一) 与 CSORT 无正协同, 此轴与 CSORT 的组合关闭。
  - 对后续实验设计的建议: 不再设计 CSORT×decoder-access 组合。decorrelation 轴
    的进一步扩展只保留: loss×loss (M153-CSORT-MFP 在队) / 写回正交 (M150/M151
    在队) / 尺度范围 (M152 在队) / 全局尺度 (本 tick 设计 M154-GSC)。0.5020
    平台的系统性证据继续指向"组合不叠加", 破平台需新信息路径而非再组合。

## 6. Crash Info (if crashed)
  - 无 crash。正常 early-stop。
================================================================================
