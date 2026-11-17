================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M165-CTF-HCG-CSORT-MQH | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M165-CTF-HCG-CSORT-MQH
  - Config: configs/Quard/ctf_hcg_csort_mqh/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqh.yaml
  - Server: server-6 | GPU: 7
  - Started: not retained | Finished: 2026-09-07 09:44:45
  - Duration: N/A
  - State: stopped_unknown

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4911 | <=26    |
  | Acc@50   | N/A    | N/A     |
  | spmIOU   | N/A    | N/A     |

## 3. Convergence Summary
  - The durable record reached epoch 26/50.
  - The process disappeared before scheduler reconciliation.
  - Best durable mIoU was 0.4911.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0017.
  - vs M169 dominant hierarchy branch (0.5000): gamma = -0.0089.
  - vs champion (M95=0.5020): gamma = -0.0109.

## 5. Conclusion
  - Conclusion: [effectively tied with baseline].
  - Interpretation: averaging hierarchy occupancy without branch topology
    dilutes target-specific evidence.
  - Recommendation: close generic hierarchy occupancy and continue with
    topology-constrained retrieval.

## 6. Crash Info (if crashed)
  - No durable crash signature was recovered.
  - Auto-fix attempt: N/A; the process was reconciled after three absence checks.
================================================================================
