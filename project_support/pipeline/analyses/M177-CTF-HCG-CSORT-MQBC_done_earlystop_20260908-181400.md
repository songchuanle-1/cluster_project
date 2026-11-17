================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M177-CTF-HCG-CSORT-MQBC | State: done_earlystop
================================================================================

## 1. Basic Info
- ID: M177-CTF-HCG-CSORT-MQBC
- Config: configs/Quard/ctf_hcg_csort_mqbc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqbc.yaml
- Server: server-4 | GPU: 0
- Started: 2026-09-08 01:08:51 | Trainer finished: 2026-09-08 17:21:15
- Duration: 16h 12m 24s | State: done_earlystop
- Registry finished_at records reconciliation time, not trainer termination.
- Source: Checkpoints/server-4/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqbc/20260908_010850/20260908_010850.log

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | 0.4962787926 | 17 |
| Acc@50 | 0.548 (rounded) | 17 |
| spmIOU | 0.459 (rounded) | 17 |
- Startup profile: 10.179092908G FLOPs. This exceeds the goal's <=10.0G limit;
  previous design assertions of compliance are not sufficient evidence.
- Startup timing uses warmup3/repeat10, not the required warmup20/repeat100.

## 3. Convergence Summary
- Exactly 27 completed validations. Best at epoch17; epochs18-27 did not improve.
- Final mIoU: 0.4826207161. Trainer explicitly logged normal early stop at17:21:15.
- The 11:17 precise-parser repair preserved the small epoch17 improvement hidden
  by rounded stdout. This run reached ten genuine post-best validations, unlike M174.
- No model crash or monitor kill occurred in this tick.

## 4. Comparison
- vs baseline model_base1=0.4894: +0.0068787926.
- vs champion M95=0.5020: -0.0057212074.
- vs M169 hierarchy branch=0.5000: -0.0037212074.
- vs M174 soft consensus exact0.4934916496: +0.0027871430.
- M169/M174 stopping histories are compromised; cross-run comparisons are
  descriptive, not proof of causality or statistical significance.

## 5. Conclusion
- Positive relative to baseline, below champion and the observed M169 peak.
- Full-path minimum support is not supported as a superior selection mechanism.
  Do not expand bottleneck score variants or tune its temperature/weights.
- Retain the already designed alternative topology tests, subject to efficiency
  audit. Any new candidate must demonstrate resource compliance before enqueue.
- Preserve remote checkpoints and the exact log; multi-seed robustness untested.

## 6. Crash Info (if crashed)
- No crash. Training terminated normally at its configured patience.
- Delayed registry reconciliation used explicit terminal evidence without
  manufacturing three deathwatch ticks. The successor M178 slot is preserved.
================================================================================
