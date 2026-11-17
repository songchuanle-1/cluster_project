================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M167-CTF-HCG-CSORT-MQX | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M167-CTF-HCG-CSORT-MQX
  - Config: configs/Quard/ctf_hcg_csort_mqx/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqx.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-09-04 13:57:43 | Finished: 2026-09-05 06:08:00
  - Duration: approximately 16h 10m
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4910 | 17      |
  | Acc@50   | 0.541  | 17      |
  | spmIOU   | 0.4560 | 17      |

## 3. Convergence Summary
  - Best first reached at epoch 17.
  - Early stopping occurred at epoch 24 with no_improve=13 against patience=10.
  - The final logged validation mIoU was 0.4870 versus historical best 0.4910.
  - Training rose normally, then oscillated around 0.478-0.489 without a late gain.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0016, below the +0.002 branch-retention threshold.
  - vs aligned mask retrieval (M161=0.4920): gamma = -0.0010.
  - vs shuffled mask retrieval (M162=0.4980): gamma = -0.0070.
  - vs champion (M95=0.5020): gamma = -0.0110.

## 5. Conclusion
  - Conclusion: [flat versus baseline, failed].
  - Interpretation: suppressing points jointly claimed by rival queries does not
    recover useful object-specific context; query collision is not the active
    bottleneck in this retrieval family.
  - Recommendation: close exclusive query ownership and continue with hierarchy
    structure and counterfactual tests already in the queue.

## 6. Crash Info (if crashed)
  - No crash. Normal patience-based early stop.
  - Log pull failed, but metrics were recovered directly from the remote log.
================================================================================
