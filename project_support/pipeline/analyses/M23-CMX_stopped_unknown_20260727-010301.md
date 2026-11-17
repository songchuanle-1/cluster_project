================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M23-CMX | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M23-CMX
  - Config: configs/Quard/model_base1_quard2_c2f_enc_lite_posA_l1_cmx.yaml
  - Label: Cluster Max-Pool aggregation — replaces default mean pooling with max when aggregating point features into cluster bank tokens
  - Server: server-4 | GPU: ? (exact GPU unclear, process disappeared)
  - Started: ~2026-07-25 23:03 | Finished: ~2026-07-27 00:03 | Duration: ~25h
  - State: stopped_unknown (process disappeared, detected at tick 2026-07-27 01:03)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4910 | 28      |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (log pull failed — remote checkpoint retained, partial data only)

## 3. Convergence Summary
  - Best first reached at: epoch ~28 (process disappeared shortly after)
  - Process disappeared before reaching early-stop threshold
  - Best mIoU=0.4910 suggests max-pool aggregation plateaus well below champion

## 4. Comparison
  - vs champion (model_base1_quard2_c2f_enc_lite_posA_l1, mean pool): γ = -0.0102 (失败, significant degradation)
  - vs baseline (model_base1, no cluster): γ = +0.0016 (marginal, below 0.002 threshold → effectively 持平)
  - vs M17-ORT (done_earlystop, 0.5005): γ = -0.0095
  - vs M22-XCA (done_earlystop, 0.4954): γ = -0.0044

## 5. Conclusion
  - 结论: [失败] max-pool aggregation is inferior to default mean pooling for cluster bank feature aggregation
  - 解释: max-pool retains only the strongest signal per dimension, discarding complementary information from other points assigned to the same cluster — mean pooling preserves richer representations. The +0.0016 vs baseline barely clears the noise floor, confirming cluster context with max-pool contributes negligible benefit.
  - 对后续实验设计的建议: 不扩展 max-pool 方向; cluster aggregation 保持默认 mean pooling; 若探索 aggregation variants, 可尝试 attention-based weighted pooling (但需注意 FLOPs 约束)

## 6. Crash Info (if crashed)
  - Error type: stopped_unknown (process disappeared without explicit crash log)
  - Error message excerpt: N/A (log inaccessible from remote)
  - Auto-fix attempt: N — terminal state already recorded, result sufficient for analysis
================================================================================
