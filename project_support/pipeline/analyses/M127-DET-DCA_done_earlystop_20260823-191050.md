================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M127-DET-DCA | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M127-DET-DCA
  - Config: configs/Quard/det_dca/model_base1_quard2_c2f_enc_lite_posA_l1_det_dca.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-23 06:08:43 | Finished: 2026-08-23 18:37:12 (早停 kill) | Duration: ~12.5h
  - State: done_earlystop (monitor kill PID=1207678, no_improve=11/10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4870 | 22/50   |
  | Acc@50   | —      | (日志未拉取) |
  | spmIOU   | —      | (日志未拉取) |
  (近5次验证序列: 0.4540, 0.4780, 0.4430, 0.4870, 0.4520 — Best 于第22次验证后回落)

## 3. Convergence Summary
  - Best first reached at: epoch ~22 (0.4870), 之后序列回落到 0.4520
  - Subsequent no_improve epochs: 11/10 (monitor kill)
  - Final epoch best: mIoU=0.4870 (22/50)
  - 收敛形态: 0.44-0.49 区间震荡, 顶仅 0.4870; 与同 2x2 矩阵 M123-DCA (0.4970)
    同形态但整体平台低 ~0.010, 未出现高平台

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = -0.0024 (失败 — 低于 baseline)
  - vs champion (M95-CTF-HCG-CSORT = 0.5020): γ = -0.0150
  - vs 2x2 矩阵对照:
      {context}x{DCA} = M123-CTF-HCG-DCA = 0.4970
      {detail}x{DCA} = M127-DET-DCA = 0.4870   → detail×DCA 负交互 (-0.0100 vs context×DCA)
      {context}x{DCM} = M124-CTF-HCG-DCM = 0.5010
      {detail}x{DCM} = M128-DET-DCM (running, Best=0.4870@ep13)  → 待定
  - vs detail alone (D1-detail=0.5003 / M20-DET=0.4955): detail 与 DCA 组合无协同, 反降

## 5. Conclusion
  - 结论: [失败] — detail message × decoder dedicated branch (DCA) 组合 0.4870,
    低于 baseline (-0.0024), 也低于 DCA alone (M123=0.4970, -0.0100)
  - 解释: detail 残差 message 与 DCA 独立 decoder 分支冲突 — detail 的残差式
    message 与 decoder query 直接 attend cluster context 的 cross-attention 信息
    路径重叠/干扰, 2x2 矩阵该格证伪。与 DCM 方向 (M128 running) 的叠加结果待定。
  - 对后续实验设计的建议: ① DET×DCA 格关闭, 不再复用该组合; ② M128-DET-DCM
    仍在跑, 等其终态补全 2x2 矩阵第4格; ③ 该矩阵价值有限 — DCA 单点 0.4970
    已判"有效但平台饱和", 2x2 组合格未能破顶, 若 M128 也 ≤0.502 → decoder-access
    轴探索完毕, 转向多层注入 (方向②)

## 6. Crash Info
  - Error type: N/A (早停 kill, 非 crash)
  - Auto-fix attempt: N
================================================================================
