================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M158-CTF-HCG-CSORT-PMD-SH | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M158-CTF-HCG-CSORT-PMD-SH
  - Config: configs/Quard/ctf_hcg_csort_pmd_sh/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pmd_sh.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-09-01 03:51:30 | Finished: 2026-09-02 17:39 | Duration: ~37.8h
  - State: done_earlystop (no_improve=11/10, monitor kill confirmed)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4950 | 22/50   |
  | Acc@50   | N/A    | N/A     |
  | spmIOU   | N/A    | N/A     |
  Tail sequence: 0.4520, 0.4920, 0.4570, 0.4930, 0.4570.

## 3. Convergence Summary
  - Best first reached by epoch 22.
  - Subsequent no-improve count reached 11 and triggered early stop.
  - The shuffled receiver-message control retained baseline-level context gain but
    stayed below the aligned PMD variant.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0056.
  - vs champion (M95-CTF-HCG-CSORT=0.5020): gamma = -0.0070.
  - vs aligned PMD (M157=0.4990): gamma = -0.0040.

## 5. Conclusion
  - Conclusion: [failed versus champion; informative control].
  - Interpretation: preserving PMD structure while shuffling cross-scale message
    content loses 0.0040, so semantic alignment contributes to PMD's residual gain.
    However, aligned PMD itself remains 0.0030 below the champion.
  - Recommendation: close PMD as an optimization direction, retain M157/M158 as
    evidence that content-aligned receiver messages matter but are insufficient.

## 6. Crash Info (if crashed)
  - No crash. Normal monitor early stop.
================================================================================
