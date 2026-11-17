================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M22-XCA | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M22-XCA
  - Config: configs/Quard/xca/model_base1_quard2_c2f_enc_lite_posA_l1_xca.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-07-24 23:06 | Finished: 2026-07-25 20:22 | Duration: ~21.3h
  - State: done_earlystop (note: work_dir had wrong path /data/songcl/Cluster_project/... missing /Project/, but training completed)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4954 | 13      |
  | Acc@50   | 0.550  | 13      |
  | spmIOU   | 0.461  | 13      |

## 3. Convergence Summary
  - Best first reached at: epoch 13 (mIoU=0.4954)
  - Subsequent no_improve epochs: 10 (epochs 14-23)
  - Final epoch best: mIoU=0.4910 vs historical best=0.4954
  - 收敛形态: 快速上升到ep13峰值(0.4954), 之后进入平台震荡(0.4879-0.4944), 未再刷Best, early stop at ep23
  - 序列: 0.339→0.369→0.412→0.410→0.446→0.461→0.473→0.476→0.482→0.478→0.483→0.490→**0.495**→0.491→0.494→0.488→0.492→0.489→0.494→0.488→0.491→0.488→0.491

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0060 (有效)
  - vs champion (posA_l1=0.5012): γ = -0.0058 (差于champion)
  - vs M17-ORT (0.5005): γ = -0.0051
  - vs M21-HYB (0.4898, running): γ = +0.0056 (M22 > M21 so far)
  - Cross-scale attention 有正向增益 vs baseline, 但不及 champion 和 ORT 机制

## 5. Conclusion
  - 结论: [有效但不足] — cross-scale cluster attention 相比 baseline 有效 (+0.0060), 但距 champion 仍有差距 (-0.0058)
  - 解释: 跨尺度 cluster token 交互提供了额外信息通路, 但单靠此机制不足以超越基础 context 注入
  - 对后续实验设计的建议: cross-scale 方向单独收益有限, 考虑与其他有效机制(ORT/detail)组合; M22-XCA 的 work_dir 路径 bug 需在后续 config 中修正

================================================================================
