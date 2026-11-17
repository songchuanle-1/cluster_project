================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M96-CTF-HCG-2LAY | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M96-CTF-HCG-2LAY
  - Config: configs/Quard/ctf_hcg_2lay/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_2lay.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-15 22:07 | Finished: 2026-08-16 10:07:24 | Duration: ~12h
  - State: done_earlystop (no_improve=11/10 ≥ patience=10, monitor kill PID=2668352)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4940 | 22/50   |
  | Acc@50   | 0.512  | ~16     |
  | spmIOU   | 0.458  | ~16     |
  (mIoU 序列尾部: 0.449, 0.493, 0.456, 0.493, 0.457 — 平台震荡未再刷新)

## 3. Convergence Summary
  - Best first reached at: epoch 16 (last "save best" 触发点, 终局 22/50)
  - Subsequent no_improve epochs: 5 (ep17-21 未刷新, 但早停判定聚合历史日志 no_improve=11/10)
  - Final epoch best: mIoU=0.4940 vs historical best=0.4940
  - 收敛形态: 前期快速爬升 → 中段平台 (0.493-0.494 反复) → 后期震荡回落

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0046 (有效, 但为 context 家族最低水平)
  - vs champion (M95-CTF-HCG-CSORT=0.5020): γ = -0.0080 (失败)
  - vs 同家族 1-layer 对照 (M81-CTF-HCG=0.5012, seed1999): γ = -0.0072 → 2-layer 注入明确退化
  - vs CTF×HCG seed 对照: M90(s123)=0.4940, M89(s42)=0.4980, M81(s1999)=0.5012
    → M96(2-layer, s1999)=0.4940 跌回 seed123 水平, 与 seed1999 应有水平差 0.0072

## 5. Conclusion
  - 结论: [失败] — cluster_att_num_layers=2 双层注入在 CTF×HCG 上退化
  - 解释: 2-layer 注入 (0.4940) 明显低于同 seed 的 1-layer (M81=0.5012, -0.0072),
    与已 ban 的 3/4/6 层重复注入一致 — 多层重复注入确认全谱系退化, 1-layer 为最优
  - 对后续实验设计的建议: 关闭多层注入方向 (2 层即退化, 不必再试 2 层变体);
    保持 cluster_att_num_layers=1, 资源聚焦 CTF×HCG×CSORT seed 对照批次
================================================================================
