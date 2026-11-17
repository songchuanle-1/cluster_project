================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M175-CTF-HCG-CSORT-MQHF | State: done_earlystop
================================================================================

## 1. Basic Info
- ID: M175-CTF-HCG-CSORT-MQHF
- Config: configs/Quard/ctf_hcg_csort_mqhf/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqhf.yaml
- Server: server-6 | GPU: 7
- Launch (local): 2026-09-07T09:48:11; logger start/end: 2026-09-07 01:50:59,246 / 2026-09-09 17:13:09,368.
- Duration in logger clock: 2 days, 15:22:10.122000. Server-6 uses UTC with clock offset;
  server-4 uses local clock. Do not mix clocks.
- Original fallback reconciliation time retained: 2026-09-10T04:07:13.
- State corrected from stopped_unknown using explicit normal-stop evidence;
  original history and previous ledger row retained. No duplicate CSV row.
- Source: Checkpoints/server-6/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqhf/20260907_015059/20260907_015059.log
- SHA256 verified remote/local: 80d35e7d116107bc010d01f62819e6c9b2cbb1fa40cc0dc3a104b0f6fdabf4a0.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | 0.49675261974334717 | 17 |
| Acc@50 | 0.546 | 17 |
| spmIOU | 0.461 | 17 |
Acc@50/spmIOU are rounded values paired at the exact best-mIoU epoch.
Startup FLOPs=11.175240108G exceeds10G; resource-ineligible.

## 3. Convergence Summary
- Verified actual epoch sequence1..27, one logger, no concatenated streams.
- Best first at17; ten real post-best validations through27.
- Final mIoU=0.48947519063949585, paired Acc50=0.543/spm=0.451.
- Trainer explicitly reports early stop with patience10; no crash evidence.

## 4. Comparison
- vs baseline .4894: +0.0073526197.
- vs M95 champion .5020: -0.0052473803.
- vs M169 .5000: -0.0032473803; M169 has partial-patience bias.
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
