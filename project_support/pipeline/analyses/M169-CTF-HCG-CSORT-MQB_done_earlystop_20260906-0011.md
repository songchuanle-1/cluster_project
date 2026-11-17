================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M169-CTF-HCG-CSORT-MQB | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M169-CTF-HCG-CSORT-MQB
  - Config: configs/Quard/ctf_hcg_csort_mqb/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqb.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-09-05 06:09:48 | Finished: 2026-09-06 00:07:47
  - Duration: approximately 17h 58m
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5000 | 21      |
  | Acc@50   | 0.554  | 21      |
  | spmIOU   | 0.4620 | 21      |

## 3. Convergence Summary
  - Best first reached at epoch 21.
  - Early stopping occurred at epoch 26 with no_improve=11 against patience=10.
  - Final logged mIoU was 0.4900 versus historical best 0.5000.
  - The run improved steadily to a strong plateau, then failed to break 0.5000.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0106, effective.
  - vs shuffled mask retrieval (M162=0.4980): gamma = +0.0020.
  - vs counterfactual residual (M170=0.4970): gamma = +0.0030.
  - vs champion (M95=0.5020): gamma = -0.0020.

## 5. Conclusion
  - Conclusion: [effective, near champion].
  - Interpretation: selecting one coherent fine cluster and its ancestor chain
    is the strongest prediction-conditioned retrieval mechanism so far.
  - Recommendation: retain the hierarchy-branch direction and test whether
    coarse-to-fine conditional search or full-path coherence improves selection.

## 6. Crash Info (if crashed)
  - No crash. Normal patience-based early stop.
  - Log pull failed, but metrics were recovered directly from the remote log.
================================================================================
