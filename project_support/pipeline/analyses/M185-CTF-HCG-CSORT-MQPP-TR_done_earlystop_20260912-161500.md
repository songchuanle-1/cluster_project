================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M185-CTF-HCG-CSORT-MQPP-TR | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M185-CTF-HCG-CSORT-MQPP-TR
  - Config: configs/Quard/ctf_hcg_csort_mqpp_tr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqpp_tr.yaml
  - Server: server-6 | GPU: 7
  - Registry launch: 2026-09-10T08:09:15; logger start/end: 2026-09-10 00:12:03,350 / 2026-09-12 07:17:18,661.
  - Logger duration: 2 days, 7:05:15.311000. Server-6 clock offset is not mixed with the
    local wall clock.
  - Archive: Checkpoints/server-6/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqpp_tr/20260910_001203/20260910_001203.log
  - SHA256 remote/local: 64a6ba960b50d971b57ecf2d4eb6fb193eecea526b4322f3f943b1d138a37ada
  - State: done_earlystop, explicit normal trainer early-stop marker and absent
    project process.

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4884226322174072 | 13 |
  | Acc@50   | 0.539 | 13 |
  | spmIOU   | 0.453 | 13 |

## 3. Convergence Summary
  - Best first reached at epoch 13.
  - Epochs 14..23 provide 10 genuine
    post-best validations.
  - Final epoch 23: mIoU=0.484160453081131, Acc@50=0.535,
    spmIOU=0.447.
  - Shape: rapid early rise, then a shallow fluctuating plateau below the best.
  - Explicit marker: Early stopping at epoch 23: no improvement for
    10 epochs (best=0.4884).

## 4. Comparison
  - vs baseline model_base1 0.4894491136: -0.0010264814.
  - vs champion M95-CTF-HCG-CSORT 0.5024607181549072:
    -0.0140380859.
  - vs target 0.5100: -0.0215773678.
  - vs M188-MQB-TR 0.4916: -0.0031773678, but M185 and M188
    are terminal-readout ablations of different parent topologies; the
    descriptive gap does not isolate one causal edge.
  - Admission measurement: 9.845844524G <= 10G.

## 5. Conclusion
  - Conclusion: failed as a mechanism claim.
  - Interpretation: MQPP terminal readout remained below both baseline and
    champion. This single-seed normal stop supplies no champion-level gain and
    does not explain the parent-path weakness.
  - Guidance: close this tested variant without numerical rescue, automatic
    rerun, or successor variant. Preserve FIFO M191-MQSD-TR then M193-MQHC-TR.

## 6. Crash Info
  - Not crashed. Explicit trainer early-stop marker, contiguous validations,
    process absence, and remote/local log hash agree.
  - Model auto-fix attempts: 0. Checkpoint remains remote.

================================================================================
