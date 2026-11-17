================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M124-CTF-HCG-DCM | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M124-CTF-HCG-DCM
  - Config: configs/Quard/ctf_hcg_dcm/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_dcm.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-22 17:13:37 | Finished: 2026-08-23 10:08:56 (早停 kill) | Duration: ~17h
  - State: done_earlystop (monitor kill PID=3825693, no_improve=11/10)
  - 注: monitor 日志拉取失败 (checkpoint 留远端), 仅 monitor 捕获指标可用
    (Best/epoch/近5次验证序列); Acc@50/spmIOU 待日志补齐后更新

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5010 | 26/50   |
  | Acc@50   | —      | (日志未拉取) |
  | spmIOU   | —      | (日志未拉取) |
  (近5次验证序列: 0.4500, 0.4910, 0.4530, 0.4880, 0.4500 — Best 后序列回落)

## 3. Convergence Summary
  - Best first reached at: epoch ~21-26 (0.5010), 之后序列回落到 0.4500
  - Subsequent no_improve epochs: 11/10 (monitor kill)
  - Final epoch best: mIoU=0.5010 (26/50)
  - 收敛形态: 0.45-0.49 区间震荡, 高平台短暂达到后回落; 与 M123-DCA 同形态但顶更高
    (0.5010 vs 0.4970), 稳定性弱 (序列波动 ~0.04)

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = +0.0116 (有效)
  - vs champion (M95-CTF-HCG-CSORT = 0.5020): γ = -0.0010 (持平平台, 未破 champion)
  - vs decoder-access 同轴 M123-DCA (0.4970): +0.0040 — DCM > DCA
  - vs 平台对照: MFP M119=0.5020, CSORT-MSG M109=0.5010, MLay M86=0.5010,
    MEMBANK-S123 M114=0.5010 — 多个独立机制均收敛于 0.501-0.502 平台, 无一破顶

## 5. Conclusion
  - 结论: [有效但平台饱和] — DCM (decoder qla KV extended memory access) 0.5010,
    高于 baseline (+0.0116), 持平 champion (-0.0010), 未破顶
  - 解释: decoder-access 轴 (用户 08-10 批准突破方向①) 的最优实现为 DCM (0.5010),
    优于 DCA (0.4970) — decoder 以共享 KV memory 方式访问 cluster context 优于独立
    cross-attention 分支; 但二者均收敛于 ~0.501-0.502 平台, 与 MFP/MLay/CSORT-MSG 等
    多个机制同平台饱和, 平台值 ~0.501-0.502 已是 seed-1999 结构上限
  - 对后续实验设计的建议: ① M126-MLAY-DCM / M128-DET-DCM 依赖已解除 (M124 终态),
    排队验证 DCM 与 MLay/detail 的叠加是否破顶; ② M129/M130 MFP seed 对照判定
    M119=0.5020 tie 是机制性还是 seed-1999 红利; ③ 若叠加后仍 ≤0.502, decoder-access
    轴已充分探索, 转向多层注入 (方向②) 或全新的 decoder query 调制信息路径

## 6. Crash Info
  - Error type: N/A (早停 kill, 非 crash)
  - Auto-fix attempt: N
================================================================================
