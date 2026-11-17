================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M24-ORT-D | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M24-ORT-D
  - Config: configs/Quard/ort/model_base1_quard2_c2f_enc_lite_posA_l1_ort_detail.yaml
  - Label: ORT orthogonality + detail message_type combination
  - Server: server-4 | GPU: 0
  - Started: 2026-07-26 08:03 | Finished: 2026-07-27 04:54 | Duration: ~20.9h
  - State: done_earlystop (clean early-stop at epoch 27, PID confirmed DEAD at tick check)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4955 | 17      |
  | Acc@50   | 0.550  | 17      |
  | spmIOU   | 0.458  | 17      |

## 3. Convergence Summary
  - Best first reached at: epoch 17 (mIoU=0.4955)
  - Subsequent no_improve epochs: 10 (epochs 18-27)
  - Final epoch (27) mIoU: 0.4850 vs best 0.4955
  - Convergence pattern: gradual rise to 0.4955@ep17, then slow oscillation and decline, no improvement for 10 consecutive epochs. Early stopping triggered end of epoch 27.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0061 (effective, but marginal)
  - vs champion (posA_l1=0.5012): gamma = -0.0057 (significantly worse)
  - vs ORT alone (M17-ORT=0.5005): gamma = -0.0050 (ORT+detail < ORT alone)
  - vs detail alone (D1-detail=0.5003): gamma = -0.0048 (ORT+detail < detail alone)
  - ORT+detail combination is strictly worse than either single mechanism.

## 5. Conclusion
  - Conclusion: [FAILED] — ORT+detail combination degrades both mechanisms, mIoU=0.4955 significantly below champion (delta=-0.0057)
  - Explanation: ORT orthogonality regularization and detail message_type interfere when combined. Consistent with previous combination failures: M21-HYB=0.4898, E4=0.4944. ORT alone=0.5005 (nearly champion-level), detail alone=0.5003 (nearly champion-level), but combined drops to 0.4955.
  - Recommendations:
    (a) Stop message_type dimension combination experiments (3 consecutive failures: HYB/E4/ORT-D)
    (b) Continue ORT single-mechanism direction: await M27-ORT-W5/M28-ORT-W1 weight ablation results
    (c) Cross-dimension combinations only if base mechanisms prove effective (e.g. ORT+refine if M25-REF succeeds)
    (d) ORT is currently closest single-mechanism to champion (delta=-0.0007), highest priority

================================================================================
