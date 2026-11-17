# Experiment Result Analysis - cluster_project
Experiment: M195-CTF-HCG-CSORT-CPS | Registry state: done_earlystop

## 1. Basic Info
- Config: configs/Quard/ctf_hcg_csort_cps/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cps.yaml
- Server: server-6 | GPU: 7 | repair attempt: 1
- Started: 2026-09-14 20:21:00; registry finished: 2026-09-15 21:02:05.
- Registry duration: approximately 24h41m. Actual termination time/cause unverified.
- Native evidence: pipeline/reports/M195_native_20260915-2110.log.

## 2. Best Metrics
| Metric | Value | Epoch |
|---|---|---|
| mIoU | 0.4986896216869354 | 20 |
| Acc@50 | 0.550 | 20 |
| spmIoU | 0.462 | 20 |
Native log pairs peak with the subsequent start of epoch21.
Registry0.4990 is rounded, not the exact metric.

## 3. Convergence Summary
- Best at epoch20; last completed validation epoch27: .4878784716129303.
- Native file stops at epoch28 step1410; stdout stops at step1413/4686.
- No native early-stop footer observed; seven completed validations after peak,
  not ten. Snapshot's done_earlystop classification is not independently confirmed.
- GPU7 was idle (6MiB,0%util) before this tick's diagnostic.
- Preserve registry pending targeted monitor provenance reconciliation; no blind retry.

## 4. Comparison
- Versus exact baseline .4894491136074066: +.0092405080795288.
- Versus exact M95 .5024607181549072: -.0037710964679718.
- Target .51 shortfall: .0113103783130646.
- M194 .4924 footer is lower, but its exact peak is unverified; do not infer synergy.

## 5. Conclusion
- Above baseline, below champion and target. CPS did not establish champion improvement.
- One seed and unresolved stop provenance do not prove general efficacy or failure
  of all shared-support mechanisms. No tuning descendant or retry authorized.
- Reconcile monitor terminal attribution with this exact PID/log before treating
  the result as patience-complete.
