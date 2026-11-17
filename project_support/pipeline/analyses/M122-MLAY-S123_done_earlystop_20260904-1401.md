================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M122-MLAY-S123 | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M122-MLAY-S123
  - Config: configs/Quard/mlay_s123/model_base1_quard2_c2f_enc_lite_posA_l1_mlay_s123.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-28 08:07:55 | Finished: 2026-09-04 13:58:08
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4940 | 16      |
  | Acc@50   | 0.547  | 16      |
  | spmIOU   | 0.4570 | 16      |

## 3. Convergence Summary
  - Best first reached at epoch 16.
  - Subsequent no-improve count reached 11 and triggered monitor early stop at 22/50.
  - The run remained near 0.4860-0.4940 after its peak without further improvement.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0046.
  - vs MLay seed 1999 (M86=0.5010): gamma = -0.0070.
  - vs MLay seed 42 (M120=0.4950): gamma = -0.0010.
  - vs champion (M95=0.5020): gamma = -0.0080.

## 5. Conclusion
  - Conclusion: [marginal versus baseline, failed versus champion].
  - Interpretation: MLay does not reproduce its seed-1999 peak. The seed matrix
    confirms that the apparent 0.5010 result is not a robust mechanism gain.
  - Recommendation: close MLay as a champion platform and prioritize the queued
    prediction-conditioned structural mechanisms.

## 6. Crash Info (if crashed)
  - No crash. Normal monitor early stop.
================================================================================
