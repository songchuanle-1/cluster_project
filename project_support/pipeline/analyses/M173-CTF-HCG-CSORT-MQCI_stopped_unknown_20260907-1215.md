================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M173-CTF-HCG-CSORT-MQCI | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M173-CTF-HCG-CSORT-MQCI
  - Config: configs/Quard/ctf_hcg_csort_mqci/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqci.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-09-06 14:35:15 | Finished: 2026-09-07 09:44:38
  - Duration: approximately 19h 09m
  - State: stopped_unknown

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4921 | <=25    |
  | Acc@50   | N/A    | N/A     |
  | spmIOU   | N/A    | N/A     |

## 3. Convergence Summary
  - The durable record reached epoch 25/50.
  - The process disappeared during the scheduler guard incident, preventing
    recovery of the exact best epoch and terminal convergence shape.
  - Best durable mIoU was 0.4921.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0027.
  - vs M169 dominant hierarchy branch (0.5000): gamma = -0.0079.
  - vs champion (M95=0.5020): gamma = -0.0099.

## 5. Conclusion
  - Conclusion: [marginal positive, below useful threshold].
  - Interpretation: within-cluster mask inconsistency is not a strong source
    of corrective context.
  - Recommendation: close the inconsistency branch and retain coherent
    hierarchy selection as the active direction.

## 6. Crash Info (if crashed)
  - No durable crash signature was recovered.
  - Auto-fix attempt: N/A; the process was reconciled after three absence checks.
================================================================================
