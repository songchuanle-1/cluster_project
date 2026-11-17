================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M168-CTF-HCG-CSORT-MQD | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M168-CTF-HCG-CSORT-MQD
  - Config: configs/Quard/ctf_hcg_csort_mqd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqd.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-09-04 13:57:58 | Finished: 2026-09-05 07:08:05
  - Duration: approximately 17h 10m
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4900 | 17      |
  | Acc@50   | 0.544  | 17      |
  | spmIOU   | 0.4550 | 17      |

## 3. Convergence Summary
  - Best first reached at epoch 17 and was matched later without improvement.
  - Early stopping occurred at epoch 23 with no_improve=11 against patience=10.
  - Final logged mIoU was 0.4880 versus historical best 0.4900.
  - Training converged normally but plateaued around 0.486-0.490.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0006, effectively flat.
  - vs M167 exclusive ownership (0.4910): gamma = -0.0010.
  - vs shuffled mask retrieval (M162=0.4980): gamma = -0.0080.
  - vs champion (M95=0.5020): gamma = -0.0120.

## 5. Conclusion
  - Conclusion: [flat versus baseline, failed].
  - Interpretation: signed mask support gained and lost between decoder layers
    does not provide a useful recurrent correction signal.
  - Recommendation: close decoder-time mask delta retrieval and keep the
    hierarchy-structure and counterfactual branches already running or queued.

## 6. Crash Info (if crashed)
  - No crash. Normal patience-based early stop.
  - Log pull failed, but metrics were recovered directly from the remote log.
================================================================================
