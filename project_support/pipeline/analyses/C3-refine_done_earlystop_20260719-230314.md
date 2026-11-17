================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: C3-refine | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: C3-refine
  - Config: configs/Quard/model_base1_quard2_c2f_enc_lite_posA_l1_refine.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-07-19T10:15 | Finished: 2026-07-19T23:01 | Duration: ~13h
  - State: done_earlystop (手动 kill, ep25)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4931 | ~17     |
  | Acc@50   | 0.496  | —       |
  | spmIOU   | 0.448  | —       |

## 3. Convergence Summary
  - Best first reached at: epoch ~17 (0.4931)
  - Subsequent no_improve epochs: 8 (0.4872→0.4916→0.4855→0.4896→0.4834→0.4813→0.4857→0.4849)
  - 收敛形态: warmup 后 ep~17 见顶 0.4931，之后震荡下行至 0.48 区间

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0037 (有效)
  - vs champion (PosA_l1=0.5012): γ = -0.0081 (未超越)
  - vs B5-residual (0.4944): γ = -0.0013
  - vs D1-detail (0.4975): γ = -0.0044

## 5. Conclusion
  - 结论: [有效但弱] — MultiScale_Gather_Refine (cluster token self-attn + sigmoid gate + distance cue) +0.0037 vs baseline
  - 解释: refine 机制单独收益有限 (0.4931)，低于 layerscale(0.4998) 和 residual(0.4944)。sigmoid gate 可能稀释了信息
  - 对后续实验设计的建议: refine 方向收益低于 layerscale/residual, 不优先组合
================================================================================
