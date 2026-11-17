================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M170-CTF-HCG-CSORT-MQR | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M170-CTF-HCG-CSORT-MQR
  - Config: configs/Quard/ctf_hcg_csort_mqr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqr.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-09-05 07:08:50 | Finished: 2026-09-05 23:07:52
  - Duration: approximately 15h 59m
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4970 | 15      |
  | Acc@50   | 0.544  | 15      |
  | spmIOU   | 0.4620 | 15      |

## 3. Convergence Summary
  - Best first reached at epoch 15.
  - Early stopping occurred at epoch 21 with no_improve=11 against patience=10.
  - Final logged mIoU was 0.4920 versus historical best 0.4970.
  - Training converged normally but did not resume improvement after epoch 15.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0076, effective.
  - vs shuffled mask retrieval (M162=0.4980): gamma = -0.0010.
  - vs M169 dominant hierarchy branch active best (0.5000): gamma = -0.0030.
  - vs champion (M95=0.5020): gamma = -0.0050.

## 5. Conclusion
  - Conclusion: [effective versus baseline, below champion].
  - Interpretation: subtracting a rolled equal-distribution context recovers a
    meaningful object-specific residual, supporting the claim that generic
    scene/distribution context contaminates direct mask retrieval.
  - Recommendation: retain the counterfactual result as positive evidence, but
    do not expand before the stronger hierarchy branch and queued tests finish.

## 6. Crash Info (if crashed)
  - No crash. Normal patience-based early stop.
  - Log pull failed, but metrics were recovered directly from the remote log.
================================================================================
