================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M164-CTF-HCG-CSORT-MQU | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M164-CTF-HCG-CSORT-MQU
  - Config: configs/Quard/ctf_hcg_csort_mqu/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqu.yaml
  - Server: server-6 | GPU: 7
  - Started: not retained | Finished: 2026-09-07 09:44:42
  - Duration: N/A
  - State: stopped_unknown

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4950 | <=27    |
  | Acc@50   | N/A    | N/A     |
  | spmIOU   | N/A    | N/A     |

## 3. Convergence Summary
  - The durable record reached epoch 27/50.
  - The process disappeared before scheduler reconciliation.
  - Best durable mIoU was 0.4950.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0056.
  - vs M169 dominant hierarchy branch (0.5000): gamma = -0.0050.
  - vs champion (M95=0.5020): gamma = -0.0070.

## 5. Conclusion
  - Conclusion: [positive but below active hierarchy branch].
  - Interpretation: uncertainty-focused retrieval carries some useful
    boundary evidence but does not localize the object as effectively as a
    coherent hierarchy branch.
  - Recommendation: retain as supporting evidence only; do not expand.

## 6. Crash Info (if crashed)
  - No durable crash signature was recovered.
  - Auto-fix attempt: N/A; the process was reconciled after three absence checks.
================================================================================
