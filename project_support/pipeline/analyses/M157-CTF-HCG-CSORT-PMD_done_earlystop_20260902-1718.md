================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M157-CTF-HCG-CSORT-PMD | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M157-CTF-HCG-CSORT-PMD
  - Config: configs/Quard/ctf_hcg_csort_pmd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pmd.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-09-01 11:55:02 | Finished: 2026-09-02 02:00:06 | Duration: ~14.1h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4990 | 26/50   |
  | Acc@50   | N/A    | N/A     |
  | spmIOU   | N/A    | N/A     |
  Secondary metrics are unavailable because the monitor did not pull a local log.

## 3. Convergence Summary
  - Best recorded by the terminal ledger: mIoU=0.4990 at 26/50.
  - Early-stopped after 11 consecutive validations without a new best.
  - Receiver-side point-message decorrelation retained most context benefit but did not break the plateau.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0096.
  - vs champion (M95-CTF-HCG-CSORT=0.5020): gamma = -0.0030.

## 5. Conclusion
  - Conclusion: [effective versus baseline, failed versus champion].
  - Interpretation: moving decorrelation to delivered point messages is viable but weaker than token-level CSORT; the pending shuffled control M158 will determine whether its residual gain is content-driven.
  - Recommendation: wait for M158, then close or retain PMD only as mechanistic evidence.

## 6. Crash Info (if crashed)
  - No crash. Normal early stop.
================================================================================
