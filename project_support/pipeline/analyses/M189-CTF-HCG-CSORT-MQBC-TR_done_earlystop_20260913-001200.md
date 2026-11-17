================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M189-CTF-HCG-CSORT-MQBC-TR | State: done_earlystop
================================================================================

## 1. Basic Info
- ID: M189-CTF-HCG-CSORT-MQBC-TR
- Config: configs/Quard/ctf_hcg_csort_mqbc_tr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqbc_tr.yaml
- Server: server-4 | GPU: 1
- Started (logger): 2026-09-12 03:07:30,104
- Finished (logger): 2026-09-13 00:00:55,147; local registry launch: 2026-09-12T03:07:33.
- State: done_earlystop. Explicit trainer marker; no surviving matching process.
- Archive: Checkpoints\server-4\model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqbc_tr\20260912_030730\20260912_030730.log; SHA256 remote/local: 88dd6356aecbaa571640a369733596c475ea42a5dd8fa09ded69c7f582b73ed3.
- Duration: approximately 20h53m from logger start to finish.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | 0.49086183309555054 | 19 |
| Acc@50 | 0.542 | 19 |
| spmIOU | 0.452 | 19 |

## 3. Convergence Summary
- Best first reached at19; ten subsequent validations did not improve.
- Final epoch29: mIoU=0.4804200530052185, Acc@50=0.531, spmIOU=0.443.
- All29 contiguous validations report9508 expressions. No crash or monitor kill.
- Initial improvement followed by a fluctuating lower plateau.

## 4. Comparison
- Baseline 0.4894491136074066: delta=+0.0014127195.
- M95 0.5024607181549072: delta=-0.0115988851.
- M177 parent .4962787926197052@17/27: delta=-0.0054169595.
- M1899.845844524G is eligible under10G; parent exceeds10G and is historical only.
- Source audit reports recurrence-only change, unchanged numerical YAML.
  Single seed, unverified environment matching and unequal realized horizons
  prevent a causal or statistically reliable conclusion.
- Prior common27-epoch comparison gives the same best delta; parent raw log
  provenance: reports/control_provenance_20260912-201000/audit.json.

## 5. Conclusion
- Failed to improve champion or parent; small +.0014127 vs baseline is below
  the .002 branch threshold. Close without retry or successor.
- Six completed preserved terminal controls M184-M189 now have0/6 above M95.
  This supplies legacy evidence, not an independently novel mechanism.
- Preserve M190/M191 trainers and remaining M193 FIFO. No test-set claim.

## 6. Crash Info
- Not crashed; repair attempts0. Checkpoints remain remote.
================================================================================
