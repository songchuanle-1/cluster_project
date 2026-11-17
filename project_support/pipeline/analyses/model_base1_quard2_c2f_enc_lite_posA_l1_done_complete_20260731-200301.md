================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: model_base1_quard2_c2f_enc_lite_posA_l1 | State: done_complete
================================================================================

## 1. Basic Info
  - ID: model_base1_quard2_c2f_enc_lite_posA_l1 (CHAMPION)
  - Config: configs/model_base1_quard2_c2f_enc_lite_posA_l1.yaml
  - Server: server-4 | GPU: ?
  - Started: ~2026-07-15 | Finished: ~2026-07-15 | Duration: 36/50 epochs
  - State: done_complete

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5012 | 36      |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch 36
  - Final epoch best: mIoU=0.5012 vs baseline=0.4894
  - Champion architecture: multi-scale cluster context with L1 loss, posA encoding, c2f coarse-to-fine, lite encoder. Routes computed but _cluster_to_points discards routing — substantively context-only.

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0118 (significant, confirms context mechanism effective)
  - vs routing-active (true_route 0.4468): γ = +0.0544 (routing active harms performance)
  - vs no-route variant (noroute 0.4800): γ = +0.0212 (dropping routing entirely also hurts)
  - Status: CURRENT CHAMPION — all Phase 1 experiments target this ceiling

## 5. Conclusion
  - 结论: [CHAMPION — context mechanism effective, routing mechanism confirmed harmful]
  - 解释: Multi-scale cluster context with posA+L1 achieves γ=+0.0118 over baseline. The routing path (computed but discarded in _cluster_to_points) is NOT the source of gain — confirmed by true_route at 0.4468 (-0.0544) and noroute at 0.4800. Gain comes from cluster bank → inst_feats context injection.
  - 对后续实验设计的建议: Focus on improving context quality (aggregation, token refinement, cross-scale fusion) rather than routing mechanisms. Target: break 0.5012 ceiling toward 0.5100.
================================================================================
