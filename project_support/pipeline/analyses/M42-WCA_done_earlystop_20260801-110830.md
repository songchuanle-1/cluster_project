================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M42-WCA | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M42-WCA
  - Config: configs/Quard/wca/model_base1_quard2_c2f_enc_lite_posA_l1_wca.yaml
  - Server: server-4 | GPU: 0
  - Started: ~2026-07-29 (estimated from tick reports) | Finished: ~2026-08-01 10:xx | Duration: ~2.5 days
  - State: done_earlystop (no_improve=10/10, patience=10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4890 | ~25     |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (Final validation sequence: 0.4818→0.4819→0.4701→0.4772→0.4745 — declining trend after Best)

## 3. Convergence Summary
  - Best first reached at: epoch ~25
  - Subsequent no_improve epochs: 10 (early-stopped at patience=10)
  - Final epoch best: mIoU=0.4890
  - Convergence pattern: peaked at ~ep25 at 0.4890, then entered steady decline. WCA weighted aggregation failed to sustain performance — the learned weights likely overfit to initial validation distribution.

## 4. Comparison
  - vs baseline (model_base1, 0.4894): γ = -0.0004 ≈ 持平 (essentially baseline performance)
  - vs champion (posA_l1, 0.5012): γ = -0.0122 (显著低于 champion)
  - vs DRP (M32-DRP, 0.5012): γ = -0.0122 (DRP alone achieves 0.5012; weighted pooling degrades it)
  - vs CTF (M41-CTF, 0.4995): γ = -0.0105 (CTF token refinement > WCA weighted aggregation)
  - Mechanism: cluster_pool_type=weighted + cluster_mode=drp. The weighted aggregation learns per-cluster attention weights for pooling, but this appears to introduce noise rather than signal — the mean pooling (DRP default) already works well and the learnable weights overfit.

## 5. Conclusion
  - 结论: [失败] — weighted cluster aggregation degrades DRP performance by 0.0122
  - 解释: The learned weighting mechanism for cluster token aggregation is counterproductive. Mean pooling (DRP's default) provides stable aggregation without overfitting. This is the second instance of "learned weighting/gating" failing in the cluster context (following the gate series: cag=0.4962, cfe=0.4901, layerscale=0.4921).
  - 对后续实验设计的建议: Do not pursue learned-weight aggregation mechanisms. Stick to structural mechanisms that change information flow (new computation graphs) rather than learned numerical weights. The cluster readback mechanism itself (DRP=0.5012) is effective; the degradation comes from replacing mean pooling with learned weights.

## 6. Crash Info
  - N/A (clean early stop)
================================================================================
