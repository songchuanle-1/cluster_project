================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M187-CTF-HCG-CSORT-MQFC-TR | State: done_earlystop
================================================================================

## 1. Basic Info
- ID: M187-CTF-HCG-CSORT-MQFC-TR
- Config: configs/Quard/ctf_hcg_csort_mqfc_tr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqfc_tr.yaml
- Server: server-4 | GPU: 1 | PID: 2863721, absent at21:07 (and at21:10).
- Started: 2026-09-10 13:13:29 (registry); finished: 2026-09-11 20:31:39 (trainer early-stop marker, server-4 logger clock).
- Duration: approximately31h18m by the logger clock; server-4 clock is not the wall clock, so this is indicative only.
- Archive: Checkpoints/server-4/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqfc_tr/20260910_131327/20260910_131327.log
- SHA256: 44a7665d7b66d83171ec67713bfae2059acd4eeb5ecaa626ac0c6a73112c04df.
- State: done_earlystop, normal trainer exit, no kill signal and no crash keyword in the tail.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | 0.49029025435447693 | 17 |
| Acc@50 | 0.541 | 17 |
| spmIOU | 0.454 | 17 |
Metrics are paired with the exact best validation, not independent maxima.

## 3. Convergence Summary
- Best first reached at17; 27 contiguous completed validations.
- Epochs18..27 provide10 genuine post-best validations; unfinished epochs never count.
- Final27: mIoU0.4832720160484314, Acc@50.539, spmIOU.442.
- Shape: fast earlier rise to a shallow plateau, then only non-improving fluctuation.
- Explicit marker: Early stopping at epoch 27: no improvement for 10 epochs (best=0.4903).
- Late-training instability is visible: grad_total_norm spikes to46.3 and40.4 with
  sem_loss sign flips of order +-1.8, i.e. the plateau is not a clean stationary fit.

## 4. Comparison
- vs model_base1=.4894491136: +.0008411407 (below the .002 branch-stop threshold).
- vs M95=.5024607182: -.0121704638; vs target=.5100: -.0197097456.
- vs M186=.4944996834 (MQHT-TR): -.0042094291. M186 and M187 are terminal-readout
  ablations of different parent topologies, so the descriptive difference does not
  isolate any single intermediate-feedback edge.
- M182 (the MQFC parent) was resource-withdrawn before training; it is not an efficacy control.
- M188/M184/M185 remain unfinished; their partial metrics are not final results.
- M187 admission9.843485228G satisfies the recorded <=10G profiling criterion.

## 5. Conclusion
- Conclusion: failed as a mechanism claim.
- Interpretation: removing intermediate feedback from the MQFC topology left a single-seed
  run that is essentially flat against baseline (+.0008, under the .002 stop rule) and
  1.22 points below champion. It supplies no evidence of a champion-level structural gain
  and does not explain why the parent path was weak.
- Guidance for the next design step: close this tested variant without numerical rescue,
  automatic rerun or descendant batch; keep the declared legacy FIFO untouched. New
  mechanisms still require the measured selection error, a stepwise derivation, verified
  primary-source novelty and matched controls demanded by goal.json.

## 6. Crash Info (if crashed)
- Not crashed. Explicit trainer early-stop marker, process absence and full logger agree.
- Model auto-fix attempts:0. Checkpoints remain remote. No queue or deployment change
  was made for this experiment in the closing tick.
================================================================================
