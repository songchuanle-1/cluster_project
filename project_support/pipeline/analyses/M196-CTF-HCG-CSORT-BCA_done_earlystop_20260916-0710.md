# Experiment Result Analysis - cluster_project
Experiment: M196-CTF-HCG-CSORT-BCA | State: done_earlystop (registry)

## 1. Basic Info
- Config: configs/Quard/ctf_hcg_csort_bca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bca.yaml
- Server: server-4 | GPU: 0 | PID: 3237667.
- Started2026-09-14 22:52:42; finished2026-09-16 07:01:14, approximately32h08m.
- Registry epoch23/50; last complete validation22.
- Sources: experiment JSON; reports/M196_native_terminal_20260916.log.

## 2. Best Metrics
| Metric | Value | Epoch |
|---|---|---|
| native exact mIoU | 0.47992366552352905 | 17 |
| registry mIoU | 0.4800 | not recorded |
| Acc@50 | peak value not extracted | unknown |
| spmIoU | peak value not extracted | unknown |

## 3. Convergence Summary
- Peak17; last validation22 mIoU0.465435266494751.
- Five completed validations after peak, not claimed monitor count11.
- Native log ends epoch23 step260 without normal completion footer.
- Question20260916-070627 records termination discrepancy.
- Patience10 completion and converged plateau are not established.

## 4. Comparison
- Versus exact baseline0.4894491136074066: -0.0095254481.
- Versus exact M950.5024607181549072: -0.0225370526.
- Registry champion0.5020 is a separate statistic.

## 5. Conclusion
- No observed improvement; no retry or renamed successor admitted.
- Censored run does not universally disprove boundary conditioning.
- Preserve registry state; actual executable/log lineage audit remains pending.
- No monitor, patience, queue or global-policy changes.
