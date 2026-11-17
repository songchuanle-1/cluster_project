================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M162-CTF-HCG-CSORT-MQF-SH | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M162-CTF-HCG-CSORT-MQF-SH
  - Config: configs/Quard/ctf_hcg_csort_mqf_sh/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqf_sh.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-09-03 06:08:03 | Finished: 2026-09-03 20:10:04 | Duration: ~14.0h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4980 | 15      |
  | Acc@50   | 0.551  | 15      |
  | spmIOU   | 0.4620 | 15      |

## 3. Convergence Summary
  - Best first reached at epoch 15.
  - Subsequent no_improve count reached 11 and triggered monitor early stop at 19/50.
  - The run rose steadily to 0.4980, then oscillated between approximately
    0.4900 and 0.4960 without exceeding its best.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0086.
  - vs aligned MQF (M161=0.4920): gamma = +0.0060.
  - vs current champion (M95-CTF-HCG-CSORT=0.5020): gamma = -0.0040.

## 5. Conclusion
  - Conclusion: [effective versus baseline, failed versus champion].
  - Interpretation: fixed within-scene mask shuffling outperformed aligned
    foreground retrieval, so the useful recurrent signal is not explained by
    object-mask semantic alignment. The branch appears to carry a strong
    scene/distribution component that can obscure object-specific context.
  - Recommendation: do not claim semantic mask retrieval from the M161/M162 pair.
    Test aligned context minus an equal-distribution shuffled counterfactual to
    remove the generic scene component while retaining object-specific residual.

## 6. Crash Info (if crashed)
  - No crash. Normal monitor early stop.
================================================================================
