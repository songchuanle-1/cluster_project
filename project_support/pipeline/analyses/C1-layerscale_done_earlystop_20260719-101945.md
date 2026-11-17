================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: C1-layerscale | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: C1-layerscale
  - Config: configs/Quard/model_base1_quard2_c2f_enc_lite_posA_l1_layerscale.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-07-17T20:55 | Finished: 2026-07-18T14:33 (auto early-stop) | Duration: ~18h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4998 | 19      |
  | Acc@50   | 0.505  | —       |
  | spmIOU   | 0.451  | —       |

## 3. Convergence Summary
  - Best first reached at: epoch 19 (0.4998)
  - Subsequent no_improve epochs: 8 (ep19→...→ep27 连续下跌)
  - 收敛形态: warmup 后 ep19 见顶，之后震荡下跌至 0.4896

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0104 (有效)
  - vs champion (PosA_l1=0.5012): γ = -0.0014 (几乎持平)
  - vs old layerscale (0.4921): γ = +0.0077 (大幅提升)

## 5. Conclusion
  - 结论: [接近有效] — LayerScale 离 champion 仅差 -0.0014
  - 解释: 本次 run 显著优于旧 layerscale (0.4921)，达到 0.4998。虽然未超越 champion，但极为接近。LayerScale gate 可能在更合适的位置或与其他机制组合时有收益
  - 对后续实验设计的建议: layerscale + residual 组合可能有协同效应

## 6. Crash Info
  - 无 crash, 正常运行, 自动早停
================================================================================
