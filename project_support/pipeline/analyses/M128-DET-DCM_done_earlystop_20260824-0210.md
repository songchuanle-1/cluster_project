================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M128-DET-DCM | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M128-DET-DCM
  - Config: configs/Quard/det_dcm/model_base1_quard2_c2f_enc_lite_posA_l1_det_dcm.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-23 10:37:12 | Finished: 2026-08-24 02:07:28 (早停 kill) | Duration: ~15.5h
  - State: done_earlystop (monitor kill PID=1794680, no_improve=11/10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4990 | 23/50   |
  | Acc@50   | —      | (日志未拉取) |
  | spmIOU   | —      | (日志未拉取) |
  (近5次验证序列: 0.4570, 0.4910, 0.4560, 0.4900, 0.4520 — Best 于第23次验证后回落)

## 3. Convergence Summary
  - Best first reached at: epoch ~23 (0.4990), 之后序列回落到 0.4520
  - Subsequent no_improve epochs: 11/10 (monitor kill)
  - Final epoch best: mIoU=0.4990 (23/50)
  - 收敛形态: 0.45-0.49 区间震荡, 顶 0.4990; 与 M124-DCM (0.5010) 同形态但平台
    低 ~0.002, 未出现高于 DCM alone 的平台

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = +0.0096 (有效)
  - vs champion (M95-CTF-HCG-CSORT = 0.5020): γ = -0.0030
  - 2x2 矩阵 {context/detail} x {DCA/DCM} 已全部完成:
      {context}x{DCA} = M123-CTF-HCG-DCA = 0.4970
      {context}x{DCM} = M124-CTF-HCG-DCM = 0.5010   ← decoder-access 轴最优格
      {detail}x{DCA}  = M127-DET-DCA = 0.4870
      {detail}x{DCM}  = M128-DET-DCM = 0.4990
  - vs 同列 DCM alone (M124 = 0.5010): γ = -0.0020 → detail 对 DCM 无正叠加
  - vs 同行 detail alone (D1-detail = 0.5003 / M20-DET = 0.4955): M128 ≈ detail
    alone, 无协同; 但 M128 (0.4990) 远高于 detail×DCA (M127 = 0.4870, +0.0120)
    → detail 与 DCM 兼容、与 DCA 冲突

## 5. Conclusion
  - 结论: [有效但未破顶] — detail message × decoder shared-pathway (DCM) 组合
    0.4990, 高于 baseline (+0.0096), 但与 DCM alone (M124 = 0.5010) 持平略降,
    detail 轴在 decoder-access 机制上无正叠加。
  - 解释: detail 残差 message 与 DCM 兼容 (对比 detail×DCA 冲突的 M127 = 0.4870),
    但收益被 DCM 自身的 shared-pathway 吸收, 不产生新提升。至此 {context/detail}
    x {DCA/DCM} 2x2 矩阵四格全部完成 — 最佳格 {context}x{DCM} = 0.5010, 与
    MLay (M86 = 0.5010) 同平台, decoder-access 轴探索完毕, 无格破 ~0.501 平台。
  - 对后续实验设计的建议: ① decoder-access 轴 (DCA/DCM) 关闭, 不再跑该方向组合;
    ② 当前唯一破平台候选为 MFP (M119 = 0.5020 tie, 待 M129-S42/M130-S123
    seed 矩阵判定是否 seed-1999 红利, CSORT 先例); ③ M131-MFP-DCM /
    M132-MFP-MLAY 均 conditional on MFP seed, 若 MFP 被证伪则撤回。

## 6. Crash Info
  - Error type: N/A (早停 kill, 非 crash)
  - Auto-fix attempt: N
================================================================================
