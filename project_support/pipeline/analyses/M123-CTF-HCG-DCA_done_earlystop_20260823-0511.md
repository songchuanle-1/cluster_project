================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M123-CTF-HCG-DCA | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M123-CTF-HCG-DCA
  - Config: configs/Quard/ctf_hcg_dca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_dca.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-22 16:11:08 | Finished: 2026-08-23 05:08:41 (早停 kill) | Duration: ~13h
  - State: done_earlystop (monitor kill PID=3698302, no_improve=11/10)
  - 注: monitor 日志拉取失败 (checkpoint 留远端), 仅 monitor 捕获指标可用
    (Best/epoch/近5次验证序列); Acc@50/spmIOU 待日志补齐后更新

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4970 | 22/50   |
  | Acc@50   | —      | (日志未拉取) |
  | spmIOU   | —      | (日志未拉取) |
  (近5次验证序列: 0.4580, 0.4890, 0.4510, 0.4970, 0.4600 — Best 于第22次验证后回落)

## 3. Convergence Summary
  - Best first reached at: epoch ~22 (0.4970), 之后序列回落到 0.4600
  - Subsequent no_improve epochs: 11/10 (monitor kill)
  - Final epoch best: mIoU=0.4970 (ep22)
  - 收敛形态: 波动较大 (0.45-0.49 区间震荡), 第22次验证刷 0.4970 顶后未再刷新,
    连续 11 次无改进 → 早停。收敛形态不稳定, 非单调上升。

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = +0.0076 (有效)
  - vs champion (M95-CTF-HCG-CSORT = 0.5020): γ = -0.0050 (未破 champion)
  - vs decoder-access 同轴 M124-DCM (running, Best=0.4990@ep18): DCM 暂领先 +0.0020
  - 对照轴: 用户 08-10 批准的两条突破方向之一 "cluster context 调制 decoder query"
    — M123-DCA = decoder query 直接 attend cluster context (cross-attention)

## 5. Conclusion
  - 结论: [持平偏弱] — DCA (decoder query→cluster cross-attention) 单点 0.4970,
    高于 baseline (+0.0076) 但低于 champion (-0.0050)
  - 解释: 0.4970 落在已知 seed-1999 机制均值 (~0.498, 见 M119 分析) 附近, 说明
    decoder query 直接 attend cluster context 既不产生明显增益也不伤害主任务 —
    该机制轴"有效但不破平台"。收敛序列波动大 (0.46-0.49), 稳定性弱于 DCM。
  - 对后续实验设计的建议: ① DCM (M124) 仍在跑且暂领先, 先看 DCM 终态再判该轴
    走向; ② M125/M126 (MLay×DCA/DCM) 与 M127/M128 (DET×DCA/DCM) 排队中, 用于
    交叉验证 DCA/DCM 与其它机制的组合; ③ 若 DCM 终态也 ≤0.499 → decoder-access
    轴与 MFP 同属"种子红利无关、机制性持平", 应转向多层注入方向

## 6. Crash Info
  - Error type: N/A (早停 kill, 非 crash)
  - Auto-fix attempt: N
================================================================================
