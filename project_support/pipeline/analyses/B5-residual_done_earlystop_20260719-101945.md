================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: B5-residual | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: B5-residual
  - Config: configs/Quard/model_base1_quard2_c2f_enc_lite_posA_l1_residual.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-07-18T15:36 | Finished: 2026-07-19T10:15 | Duration: ~19h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4944 | ~24     |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch ~24 (0.4944)
  - Subsequent no_improve epochs: 5+ (0.4944→...→0.4819→0.4769→0.4743)
  - Final epoch 29 best: 0.4777 vs historical best=0.4944
  - 收敛形态: 缓慢上升至 ep24 见顶 0.4944，之后快速下跌至 0.47 区间

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0050 (有效)
  - vs champion (PosA_l1=0.5012): γ = -0.0068 (未超越)
  - vs l1 (0.5006): γ = -0.0062

## 5. Conclusion
  - 结论: [有效] — ResidualAttnRefine 补 Q/K/V 梯度流有效 (+0.0050 vs baseline)
  - 解释: residual 调制显著优于无 residual 变体，但未达到 champion 水平。与 layerscale(0.4998) 结合可能有协同效应
  - 对后续实验设计的建议: 考虑 residual + refine 组合

## 6. Crash Info
  - 首次 3 次 crash: gorilla Criterion 重复注册 (force=True 修复)
  - 第 4 次手动推送成功
================================================================================
