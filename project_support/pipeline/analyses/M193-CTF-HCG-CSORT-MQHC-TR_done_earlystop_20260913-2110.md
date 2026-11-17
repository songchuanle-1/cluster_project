# Experiment Result Analysis - cluster_project
Experiment: M193-CTF-HCG-CSORT-MQHC-TR | State: done_earlystop

## 1. Basic Info
- Config: configs/Quard/ctf_hcg_csort_mqhc_tr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqhc_tr.yaml
- Server: server-4 | GPU: 0.
- Log start: 2026-09-13 02:07:53.283; finish: 20:21:49.050.
- Duration: 18:13:55.767; queue launch: 02:07:55.
- Scientific terminal state confirmed by explicit normal stop and absent process.
- Registry finalized done_earlystop by normal monitor deathwatch3/3 at
  2026-09-13 23:08:50; running registry is empty. No counter acceleration.
- Raw log: reports/tick_evidence_20260913-2110/M193.log.
- Archive verified23:10: Checkpoints/server-4/
  model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqhc_tr/
  20260913_020753/20260913_020753.log; ledger log_local repaired under lock.
- SHA256: 1dd701c5715610a95e41ee6d60a96ede3a0ab2d2e2d2b9aa580c50583d8a079e.

## 2. Best Metrics
| Metric | Value | Epoch |
|--------|-------|-------|
| mIoU | 0.4906114339828491 | 17 |
| Acc@50 | 0.543 | 17 |
| spmIOU | 0.454 | 17 |

## 3. Convergence Summary
- 27 precise mIoU records; peak17 followed by10 non-improving validations.
- Final27: mIoU .4784739911556244, Acc50 .532, spmIOU .439.
- Final evaluation contains9508 expressions.
- Explicit marker: Early stopping at epoch27, no improvement for10 epochs.
- No crash, monitor kill, restart or patience change this tick.

## 4. Comparison
- Baseline .4894491136074066: +.0011623203754425.
- Champion M95 .5024607181549072: -.0118492841720581.
- Target .5100: -.0193885660171509.
- Parent M174 .49349164962768555: -.00288021564483645.
- M174 had only5 genuine stale validations before a historical parser-induced
  stop; it is not a matched full-patience control. No isolated causal claim.
- Recorded admission9.885821484G is historical, not a fresh resource measurement.

## 5. Conclusion
- Failed to improve champion; gain over baseline is below .002.
- Close M193 without automatic successors, tuning or reruns.
- M184-M191 plus M193:0/9 terminal controls exceed M95.
- Original mechanism admission remains incomplete; idle GPUs do not authorize refill.

## 6. Crash Info
- Not crashed; training repair attempts0.
- Monitor registry reconciliation completed. Automatic log pull failed;
  existing raw capture matches remote SHA256 and is used for archive repair.
