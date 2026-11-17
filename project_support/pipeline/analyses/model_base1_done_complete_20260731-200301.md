================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: model_base1 | State: done_complete
================================================================================

## 1. Basic Info
  - ID: model_base1
  - Config: configs/model_base1.yaml
  - Server: server-4 | GPU: ?
  - Started: ~2026-06-27 | Finished: ~2026-06-27 | Duration: ~41 epochs
  - State: done_complete

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4894 | 41      |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch 41
  - Final epoch best: mIoU=0.4894
  - Baseline model without cluster mechanism. Reached 0.4894 at epoch 41/50, steady convergence.

## 4. Comparison
  - Role: BASELINE — all other experiments compared against this
  - vs champion (model_base1_quard2_c2f_enc_lite_posA_l1): γ = -0.0118

## 5. Conclusion
  - 结论: [BASELINE]
  - 解释: Base model without cluster context mechanism. Serves as the reference point for all Phase 1 experiments.
  - 对后续实验设计的建议: N/A (baseline reference)
================================================================================
