================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M184-CTF-HCG-CSORT-MQST-TR | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M184-CTF-HCG-CSORT-MQST-TR
  - Config: configs/Quard/ctf_hcg_csort_mqst_tr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqst_tr.yaml
  - Server: server-6 | GPU: 7
  - Registry launch: 2026-09-10T08:09:05 (Asia/Shanghai).
  - Logger start: 2026-09-10 00:11:53,403; finish: 2026-09-12 08:35:18,559; duration: 2 days, 8:23:25.156000.
    Server-6 reports UTC, so logger finish corresponds to 2026-09-12
    16:35:18 Asia/Shanghai; do not mix logger and local naive timestamps.
  - State: done_earlystop; explicit marker, absent process, 25 validations.
  - Archive: Checkpoints/server-6/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqst_tr/20260910_001153/20260910_001153.log
  - Remote/local SHA256: b615b2f6dcacb15a2233bf48842988566a4bcdfda57932293c0d4ff1f6434c6d

## 2. Best Metrics
  | Metric | Value | @ Epoch |
  |--------|-------|---------|
  | mIoU | 0.48762595653533936 | 15 |
  | Acc@50 | 0.538 | 15 |
  | spmIOU | 0.451 | 15 |

## 3. Convergence Summary
  - Best first reached at epoch 15; epochs 16-25 all failed to improve.
  - Final epoch 25 mIoU=0.471560537815094, Acc@50=0.525, spmIOU=0.433.
  - Ten post-best validations; normal trainer patience=10 stop, no monitor kill.
  - Initial improvement followed by a fluctuating/declining plateau.
  - Exact log-derived best epoch is 15, not the live parser's progress counter.

## 4. Comparison
  - Baseline model_base1 0.4894491136074066:
    delta=-0.0018231571.
  - Champion M95 0.5024607181549072:
    delta=-0.0148347616.
  - Target 0.5100: delta=-0.0223740435.
  - M185-MQPP-TR 0.4884226322174072:
    delta=-0.0007966757; different topology,
    not a matched causal comparison.
  - M179-MQST parent never trained after >10G admission failure.
    No parent accuracy exists; recurrence-edge effect cannot be isolated.
  - M184 admission: 9.845647916G; resource eligibility is not efficacy.

## 5. Conclusion
  - Conclusion: failed to improve baseline or champion in this single-seed run.
  - The preserved MQST terminal-readout control does not retain M95's gain.
    It supplies no evidence for a new mechanism or automatic successor.
  - Close this variant without numerical rescue/retry. Preserve M191 then M193
    on server-4 and preserve live M189/M190.
  - Aggregate validation bests are exploratory; no independent test or
    mechanistic causal conclusion follows from this comparison.

## 6. Crash Info
  - Not crashed. Model repair attempts: 0. No checkpoint pulled or modified.
================================================================================
