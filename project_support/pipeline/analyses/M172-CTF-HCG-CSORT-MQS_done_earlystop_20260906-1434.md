================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M172-CTF-HCG-CSORT-MQS | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M172-CTF-HCG-CSORT-MQS
  - Config: configs/Quard/ctf_hcg_csort_mqs/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqs.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-09-06 00:08:50 | Finished: 2026-09-06 14:34:26
  - Duration: approximately 14h 26m
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4966 | 15      |
  | Acc@50   | 0.548  | 15      |
  | spmIOU   | 0.4600 | 15      |

## 3. Convergence Summary
  - Best first reached at epoch 15.
  - Early stopping occurred at epoch 21 with no_improve=11 against patience=10.
  - Final logged mIoU was 0.4924 versus historical best 0.4966.
  - The stable-support mechanism converged normally, peaked in the middle of
    training, and then oscillated below its best without renewed improvement.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0072, effective.
  - vs M170 counterfactual residual (0.4970): approximately tied.
  - vs M169 dominant hierarchy branch (0.5000): gamma = -0.0034.
  - vs champion (M95=0.5020): gamma = -0.0054.

## 5. Conclusion
  - Conclusion: [effective versus baseline, below champion].
  - Interpretation: intersecting consecutive decoder masks retrieves a useful
    persistent object core, but persistence alone removes boundary/detail
    evidence needed to match hierarchy-branch retrieval.
  - Recommendation: retain M172 as evidence for temporal support stability, but
    do not expand this branch before the stronger hierarchy candidates finish.

## 6. Crash Info (if crashed)
  - No crash. Normal patience-based early stop.
  - Exact metrics were recovered from the remote training log.
================================================================================
