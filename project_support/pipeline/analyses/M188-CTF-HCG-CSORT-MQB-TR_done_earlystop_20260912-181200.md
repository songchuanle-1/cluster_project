================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M188-CTF-HCG-CSORT-MQB-TR | State: done_earlystop
================================================================================

## 1. Basic Info
- Config: configs/Quard/ctf_hcg_csort_mqb_tr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqb_tr.yaml
- Server: server-4 | GPU: 0 | State: done_earlystop (already archived).
- Logger start: 2026-09-11 03:14:07.601000; finish: 2026-09-12 04:04:56.878000; duration: 1 day, 0:50:49.277000.
  Server-4 clock verified +08:00. Registry launch 2026-09-11 03:14:09 and
  terminal detection 2026-09-12 04:08:31 are operational timestamps.
- Archive: Checkpoints/server-4/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqb_tr/20260911_031407/20260911_031407.log
- Remote/local SHA256: 92790e62ccd35df7fee0310ac8b5c179a7623df29fd64da27df0fe0c445ea0bc
- This evidence supplement supersedes rounded metrics and approximate final
  mIoU in the earlier M188 analysis; historical documents remain intact.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | 0.49161195755004883 | 13 |
| Acc@50 | 0.544 | 13 |
| spmIOU | 0.457 | 13 |

## 3. Convergence Summary
- 23 contiguous validations, each evaluating 9508 expressions.
- Best first reached at epoch 13; all ten later validations failed to improve.
- Final epoch 23: mIoU 0.4848948121070862, Acc@50 0.538, spmIOU 0.448.
- Initial improvement then fluctuating plateau. Explicit normal early stop;
  no retry, new transition, or checkpoint transfer.

## 4. Comparison
- Baseline model_base1 0.4894491136074066: delta +0.0021628439.
- Champion M95 0.5024607181549072: delta -0.0108487606.
- Target 0.5100: gap 0.0183880424.
- Parent M169 has ledger 0.5000 (rounded): descriptive delta about -0.0084.
  Parent raw precision and paired scene predictions are not verified here.
- M186 0.49449968338012695 is a different topology, not a matched control.

## 5. Conclusion
- Positive vs baseline, failed vs champion in this single-seed legacy run.
- Removing intermediate feedback under this configuration does not retain
  champion-level performance; this is not proof about all recurrence.
- Keep this variant closed without successor. Exact-log recovery does not
  supply a novel mechanism or independently confirm a causal claim.
- The M184-M188 synthesis remains 0/5 above M95; 4/5 parents never trained.
  All five child logs are now locally hash-verifiable. No pooled significance
  estimate is justified across different architectures.

## 6. Crash Info
- Not crashed. Model repair attempts: 0. No training or deployment edits.
================================================================================
