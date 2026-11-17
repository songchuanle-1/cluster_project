================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M188-CTF-HCG-CSORT-MQB-TR | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M188-CTF-HCG-CSORT-MQB-TR
  - Config: configs/Quard/ctf_hcg_csort_mqb_tr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqb_tr.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-09-11 03:14:09 | Finished: 2026-09-12 04:08:31 | Duration: 24h54m22s
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4916 | 13      |
  | Acc@50   | 0.544  | 13      |
  | spmIOU   | 0.457  | 13      |

## 3. Convergence Summary
  - Best first reached at: epoch 13
  - Subsequent no_improve epochs: 10
  - Final epoch best: mIoU=0.485 vs historical best=0.4916
  - The run rose quickly through epoch 13, then plateaued with small oscillations and early-stopped at epoch 23.

## 4. Comparison
  - vs baseline (model_base1): gamma = +0.0022 (borderline effective vs baseline)
  - vs current champion (M95-CTF-HCG-CSORT): gamma = -0.0108 (failed vs champion)
  - Related control M186-CTF-HCG-CSORT-MQHT-TR: 0.4944996834@17
  - Related legacy run M169-CTF-HCG-CSORT-MQB: evidence source for this terminal-only ablation; M188 removes intermediate query feedback.

## 5. Conclusion
  - Conclusion: [failed vs champion]
  - Explanation: The terminal-only dominant-ancestor branch replacement reached only 0.4916, so removing intermediate query feedback did not preserve the M95 mechanism's gain.
  - Recommendation: Keep this legacy terminal-readout validation closed. Do not generate a successor variant in this family; continue Phase 1 with a separately admitted mechanism or a bounded diagnostic that measures upstream decoder causality.

## 6. Crash Info
  - Error type: none
  - Error message excerpt: none
  - Auto-fix attempt: N - normal early stop, no crash
================================================================================
