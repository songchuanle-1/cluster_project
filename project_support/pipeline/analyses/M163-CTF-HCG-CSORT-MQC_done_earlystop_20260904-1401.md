================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M163-CTF-HCG-CSORT-MQC | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M163-CTF-HCG-CSORT-MQC
  - Config: configs/Quard/ctf_hcg_csort_mqc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqc.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-09-03 11:08:25 | Finished remotely: 2026-09-04 04:54:30
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4899 | 17      |
  | Acc@50   | 0.542  | 17      |
  | spmIOU   | 0.4530 | 17      |

## 3. Convergence Summary
  - Best first reached at epoch 17.
  - Early stopping occurred at epoch 27 after 10 epochs without improvement.
  - Final mIoU was 0.4800; no traceback or CUDA error was present.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0005.
  - vs M161 foreground retrieval (0.4920): gamma = -0.0021.
  - vs champion (M95=0.5020): gamma = -0.0121.

## 5. Conclusion
  - Conclusion: [flat versus baseline, failed].
  - Interpretation: explicit foreground-minus-background query contrast does not
    produce useful object-specific context and does not break the plateau.
  - Recommendation: close the MQC contrast branch.

## 6. Crash Info (if crashed)
  - No crash. Normal training early stop.
================================================================================
