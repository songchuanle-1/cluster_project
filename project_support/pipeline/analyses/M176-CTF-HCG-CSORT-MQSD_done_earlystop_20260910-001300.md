================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M176-CTF-HCG-CSORT-MQSD | State: done_earlystop
================================================================================

## 1. Basic Info
- ID: M176-CTF-HCG-CSORT-MQSD
- Config: configs/Quard/ctf_hcg_csort_mqsd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqsd.yaml
- Server: server-6 | GPU: 7 | Previous PID: 2797120
- Registry launch: 2026-09-07 09:48:32 Asia/Shanghai, retained unchanged.
- Logger start: 2026-09-07 01:51:18.371; end: 2026-09-09 14:48:51.019,
  both in the server-6 UTC clock. Elapsed logger duration: 60h 57m 32.648s.
- Server-6 has approximately +2m48s clock offset in addition to the timezone
  difference. Do not subtract local launch time from the remote end timestamp.
- State: done_earlystop. Registry/CSV finished_at records local reconciliation
  during the 2026-09-10 00:07 tick, not the trainer's actual termination.
- Log: Checkpoints/server-6/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqsd/20260907_015118/20260907_015118.log
- Local/remote SHA256:
  87ca41800632e9425913a7b8d66a37e04d12e77b0a13e4f129dcfad2f89c7888.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | 0.4935617446899414 | 14 |
| Acc@50 | 0.541 (rounded) | 14 |
| spmIOU | 0.456 (rounded) | 14 |
All metrics are paired at the best-mIoU epoch, not independent maxima.
The exact mIoU logger and rounded summary form one 24-validation lineage.
Startup FLOPs: 10.378977708G, exceeding the goal's <=10.0G constraint.
This run is not eligible for resource-qualified promotion.

## 3. Convergence Summary
- Exactly 24 completed validations; best first reached at epoch14.
- Epochs15-24: ten genuine validations below the exact best.
- Final epoch24 mIoU=0.48384666442871094, Acc@50=.535, spmIOU=.446.
- Early rise from .3435 at epoch1 to .4936 at14, then a plateau/decline.
- Explicit final marker: "Early stopping at epoch 24: no improvement for
  10 epochs (best=0.4936)" at remote2026-09-09 14:48:51.019.
- No process found in actual Sep9 23:08 and Sep10 00:10 monitoring;
  fresh ps00:11 confirms absence. No third deathwatch observation fabricated.
- The Sep9 23:07 tick discovered the terminal marker but failed before
  reconciliation/reporting. This analysis closes that missing work.

## 4. Comparison
- vs baseline model_base1=.4894: +.0041617447.
- vs champion M95=.5020: -.0084382553.
- vs M169 dominant branch=.5000: -.0064382553.
- vs M174 exact soft consensus=.4934916496: +.0000700951.
- vs M177 full-path bottleneck=.4962787926: -.0027170479.
- M169/M174 had compromised early-stop histories. These are descriptive
  single-seed comparisons, not causal or robustness evidence.

## 5. Conclusion
- Positive relative to baseline, unsuccessful relative to the champion and
  the current resource constraint.
- Sibling-relative discrimination does not support a superior context
  selection mechanism in this run. Close this score branch without tuning
  coefficients, temperatures or revising the active models.
- Preserve the separate pre-approved terminal-topology tests and HQI run.
  This result does not establish that all cluster context is ineffective.
- Retain remote checkpoints and the exact archived log. No automatic rerun.

## 6. Crash Info (if crashed)
- No crash; normal trainer early stop. Repair attempts: 0.
- Existing finalizer used under pipeline lock, preserving M175 GPU7 ownership,
  all unrelated running entries, launch history and waiting order.
- Decision: decisions/20260910-001247_other.md.
================================================================================
