================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M160-CTF-HCG-CSORT-GEO-SH | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M160-CTF-HCG-CSORT-GEO-SH
  - Config: configs/Quard/ctf_hcg_csort_geo_sh/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_geo_sh.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-09-02 17:40:17 | Finished: 2026-09-04 21:08:07
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4910 | 16      |
  | Acc@50   | 0.546  | 16      |
  | spmIOU   | 0.4540 | 16      |

## 3. Convergence Summary
  - Best first reached at epoch 16.
  - Subsequent no-improve count reached 11 and triggered monitor early stop at 22/50.
  - Final observed mIoU was 0.4880; the run plateaued near baseline.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0016.
  - vs aligned geometry M159=0.4840: gamma = +0.0070.
  - vs champion M95=0.5020: gamma = -0.0110.

## 5. Conclusion
  - Conclusion: [flat versus baseline, failed versus champion].
  - Interpretation: shuffling geometry removes M159's damage but does not create
    a useful gain. Geometry content is harmful and the structural injection shell
    is effectively neutral.
  - Recommendation: close the direct geometry-enrichment axis.

## 6. Crash Info (if crashed)
  - No crash. Normal monitor early stop.
================================================================================
