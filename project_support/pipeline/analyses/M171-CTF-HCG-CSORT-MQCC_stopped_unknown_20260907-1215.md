================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M171-CTF-HCG-CSORT-MQCC | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M171-CTF-HCG-CSORT-MQCC
  - Config: configs/Quard/ctf_hcg_csort_mqcc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqcc.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-09-05 23:08:31 | Finished: 2026-09-07 09:44:36
  - Duration: approximately 34h 36m
  - State: stopped_unknown

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4936 | <=34    |
  | Acc@50   | N/A    | N/A     |
  | spmIOU   | N/A    | N/A     |

## 3. Convergence Summary
  - The durable record reached epoch 34/50.
  - The remote process disappeared while scheduler ticks were blocked by the
    legacy unhealthy guard, so the exact peak epoch and final trajectory are
    unavailable.
  - Best durable mIoU was 0.4936.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0042.
  - vs M169 dominant hierarchy branch (0.5000): gamma = -0.0064.
  - vs champion (M95=0.5020): gamma = -0.0084.

## 5. Conclusion
  - Conclusion: [weak positive, below active hierarchy branch].
  - Interpretation: query-context competition did not provide enough
    object-specific separation to justify extending the mechanism.
  - Recommendation: close direct query competition and prioritize hierarchy
    topology retrieval.

## 6. Crash Info (if crashed)
  - No durable crash signature was recovered.
  - Auto-fix attempt: N/A; the process was reconciled after three absence checks.
================================================================================
