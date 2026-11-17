# Experiment Result Analysis - cluster_project
Experiment: M191-CTF-HCG-CSORT-MQSD-TR | State: done_earlystop

## 1. Basic Info
- Config: configs/Quard/ctf_hcg_csort_mqsd_tr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqsd_tr.yaml
- Server: server-4 | GPU: 1.
- Logger start: 2026-09-13 00:07:59.006; finish: 2026-09-13 19:50:38.085.
- Duration: 19:42:39.079. Registry launch: 2026-09-13T00:08:01.
- Explicit normal trainer early-stop marker; process absent at19:51.
- Archive: Checkpoints/server-4/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqsd_tr/20260913_000758/20260913_000758.log
- Raw archive hash and closure validation: reports/source_head_interference_20260913-1938/m191_closure.json.

## 2. Best Metrics
| Metric | Value | Epoch |
|--------|-------|-------|
| mIoU | 0.4917144179344177 | 15 |
| Acc@50 | 0.541 | 15 |
| spmIOU | 0.457 | 15 |

## 3. Convergence Summary
- 25 contiguous completed validations, each9508 expressions.
- Best at15, then10 consecutive non-improving validations.
- Final25: mIoU0.48435178399086, Acc50 .539, spmIOU .448.
- Exact trainer marker: Early stopping at epoch25, no improvement for10 epochs.
- No monitor kill, crash or rescue; checkpoint remains remote.

## 4. Comparison
- Baseline .4894491136074066: +.0022653043270111.
- M95 .5024607181549072: -.0107463002204895.
- Target .51: -.0182855820655823.
- Parent M176 .4935617446899414: -.0018473267555237.
- Parent ran on server-6; child on server-4. Unverified environment matching
  prevents a strict isolated causal claim about intermediate feedback.
- Recorded admission FLOPs9.885821484G; this is not a new efficiency profile.

## 5. Conclusion
- Above baseline but failed to improve the champion; close the tested variant.
- M184-M191 terminal controls now0/8 above M95. M193 remains running.
- No automatic successor, rerun, numerical rescue or queue refill.

## 6. Crash Info
- Not crashed. Explicit normal stop and absent process.
- Training repair attempts0. Only evidence-gated registry reconciliation.
