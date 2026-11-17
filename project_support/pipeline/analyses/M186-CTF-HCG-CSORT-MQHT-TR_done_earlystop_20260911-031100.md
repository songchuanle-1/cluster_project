================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M186-CTF-HCG-CSORT-MQHT-TR | State: done_earlystop
================================================================================

## 1. Basic Info
- ID: M186-CTF-HCG-CSORT-MQHT-TR
- Config: configs/Quard/ctf_hcg_csort_mqht_tr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqht_tr.yaml
- Server: server-4 | GPU: 0 | PID: 1982211, absent at03:07.
- Started: 2026-09-10 08:27:11 (registry); finished: 2026-09-11 02:57:54.187 (trainer).
- Duration: approximately18h31m. State: done_earlystop, normal trainer exit, no kill.
- Archive: Checkpoints/server-4/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqht_tr/20260910_082710/20260910_082710.log
- SHA256: f1227f1c8efa52aac4cd170ee136701ff707b63d0bdefa27e1bc2741e7337623.
- Full log verification and actual epoch-paired rows: reports/m186_m188_transition_20260911.json.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | 0.49449968338012695 | 17 |
| Acc@50 | 0.548 | 17 |
| spmIOU | 0.459 | 17 |
Metrics are paired with the exact best validation, not independent maxima.

## 3. Convergence Summary
- Best first reached at17; 27 contiguous completed validations.
- Epochs18..27 provide10 genuine post-best validations; unfinished epochs never count.
- Final27: mIoU0.4796425402164459, Acc@50.535, spmIOU.441.
- Rapid early improvement followed by non-improving fluctuations below best.
- Explicit marker: Early stopping at epoch 27: no improvement for 10 epochs (best=0.4945).

## 4. Comparison
- vs model_base1=.4894: +.0050996834.
- vs M95=.5020: -.0075003166; vs target=.5100: -.0155003166.
- M181 parent topology was resource-withdrawn before training, not an efficacy control.
- M183=.4915492237 is a different mechanism; the descriptive difference does not isolate transport.
- M184/M185/M187 remain unfinished; do not rank their partial metrics as final results.
- M186 admission9.843485228G satisfies the recorded <=10G profiling criterion.

## 5. Conclusion
- Above baseline, but failed to improve champion or achieve the target.
- This single-seed terminal transport graph supplies no evidence of champion-level gain.
  It does not establish why it failed, nor falsify all hierarchy mechanisms.
- Close this tested variant without numerical rescue, automatic rerun or descendant batch.
  Preserve existing legacy FIFO; future mechanisms require measured errors, derivation,
  verified primary-paper novelty and matched controls under goal.json.

## 6. Crash Info (if crashed)
- Not crashed. Explicit normal stop, process absence and archived full logger agree.
- Model auto-fix attempts:0. Checkpoints remain remote.
================================================================================
