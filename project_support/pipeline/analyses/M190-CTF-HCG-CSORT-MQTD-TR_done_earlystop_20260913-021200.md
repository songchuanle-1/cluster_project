# Experiment Result Analysis - cluster_project
Experiment: M190-CTF-HCG-CSORT-MQTD-TR | State: done_earlystop

## 1. Basic Info
- ID: M190-CTF-HCG-CSORT-MQTD-TR
- Config: configs/Quard/ctf_hcg_csort_mqtd_tr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqtd_tr.yaml
- Server: server-4 | GPU: 0
- Started (logger): 2026-09-12 05:08:05,730; finished (logger): 2026-09-13 02:04:35,522; duration: 20:56:29.792000.
- Registry launch: 2026-09-12T05:08:08. State: done_earlystop.
- Archive: Checkpoints\server-4\model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqtd_tr\20260912_050805\20260912_050805.log; remote/local SHA256: 11dfde1a77a39241366ed6e60f828b88de03ac22ce013abd1c8b01c95d0eb808.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | 0.4890006184577942 | 14 |
| Acc@50 | 0.542 | 14 |
| spmIOU | 0.454 | 14 |

## 3. Convergence Summary
- Best first reached at14; epochs15-24 are ten strictly lower validations.
- Final epoch24: mIoU=0.4858858585357666, Acc@50=0.538, spmIOU=0.45.
- All24 contiguous validations report9508 expressions.
- Explicit trainer early-stop marker; normal stop, not monitor kill or crash.

## 4. Comparison
- Baseline 0.4894491136074066: delta=-0.0004484951.
- M95 0.5024607181549072: delta=-0.0134600997.
- M178 parent 0.49304044246673584: delta=-0.0040398240.
- Common epochs1-24 best delta=-0.0040398240; M178 full run34 epochs.
- M1909.845647916G <=10G; parent >10G, historical comparison only.
- M190 changes BOTH intermediate recurrence and real-cluster padding.
  Neither full-run nor common-horizon difference isolates recurrence.
  Single seed, unverified environment matching and validation reuse remain.
  Counts do not establish identical expression identities/order; no paired
  scene uncertainty, independent confirmation, or test-set claim.

## 5. Conclusion
- Failed to improve baseline, M95 or parent; close without retry or successor.
- Seven completed legacy terminal controls M184-M190 now0/7 above M95.
  Different topologies are not independent seed replications.
- Preserve M191 GPU1 and original M193 now running on GPU0.

## 6. Crash Info
- Not crashed; model repair attempts0. Checkpoints remain remote.
