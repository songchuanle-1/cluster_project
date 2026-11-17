================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M178-CTF-HCG-CSORT-MQTD | State: done_earlystop
================================================================================

## 1. Basic Info
- ID: M178-CTF-HCG-CSORT-MQTD
- Config: configs/Quard/ctf_hcg_csort_mqtd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqtd.yaml
- Server: server-4 | GPU: 0
- Launch (local): 2026-09-08T18:09:35; logger start/end: 2026-09-08 18:09:33,105 / 2026-09-10 00:39:56,895.
- Duration in logger clock: 1 day, 6:30:23.790000. Server-6 uses UTC with clock offset;
  server-4 uses local clock. Do not mix clocks.
- Original fallback reconciliation time retained: 2026-09-10T03:07:10.
- State corrected from stopped_unknown using explicit normal-stop evidence;
  original history and previous ledger row retained. No duplicate CSV row.
- Source: Checkpoints/server-4/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqtd/20260908_180933/20260908_180933.log
- SHA256 verified remote/local: 7ed5f5e51ca3dd086b6e65b13d7a721fcb81fa039ee44805acc198e4cea2423f.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | 0.49304044246673584 | 24 |
| Acc@50 | 0.546 | 24 |
| spmIOU | 0.455 | 24 |
Acc@50/spmIOU are rounded values paired at the exact best-mIoU epoch.
Startup FLOPs=10.178109868G exceeds10G; resource-ineligible.

## 3. Convergence Summary
- Verified actual epoch sequence1..34, one logger, no concatenated streams.
- Best first at24; ten real post-best validations through34.
- Final mIoU=0.47917425632476807, paired Acc50=0.535/spm=0.439.
- Trainer explicitly reports early stop with patience10; no crash evidence.

## 4. Comparison
- vs baseline .4894: +0.0036404425.
- vs M95 champion .5020: -0.0089595575.
- vs M169 .5000: -0.0069595575; M169 has partial-patience bias.
- Single-seed comparisons descriptive, not statistical or causal proof.

## 5. Conclusion
- Above baseline but below champion and resource-ineligible.
- This recurrent hierarchy retrieval did not improve the champion; no score,
  coefficient or depth tuning. Keep independent terminal-readout tests.
- Preserve checkpoint and evidence; no automatic rerun or model hot edit.

## 6. Crash Info (if crashed)
- No crash; model repair attempts0. Fallback metadata corrected under lock.
- Decision:20260910-075236_other.md. Previous finished_at/launch preserved.
================================================================================
