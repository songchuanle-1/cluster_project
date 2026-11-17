================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M33-DTW | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M33-DTW
  - Config: configs/Quard/dtw/model_base1_quard2_c2f_enc_lite_posA_l1_dtw.yaml
  - Label: Density-Weighted Token — cluster token 按其包含的点数加权后再回写 (log-count soft normalized)
  - Server: server-4 | GPU: 1
  - Started: 2026-07-28 08:00 | Finished: ~2026-07-29 01:31 | Duration: ~17.5h
  - State: stopped_unknown (process disappeared during epoch 30 training, PID DEAD at tick check 02:03)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4968 | 20      |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (Best=0.4968 from pipeline_monitor remote tick. DTW config matches champion except cluster_mode=dtw adds density weighting.)

## 3. Convergence Summary
  - Best first reached at: epoch 20 (mIoU=0.4968)
  - Subsequent no_improve epochs: 10 (epochs 21-30 all < 0.4968)
  - mIoU trajectory: ep1 0.3245 → ep10 0.4844 → ep13 0.4958 → ep20 0.4968(Best) → ep28 0.4857(decline) → ep30 0.4898
  - Convergence pattern: rapid initial rise (ep1-13), peak plateau (ep13-20 around 0.492-0.497), then slow decline with oscillation (ep21-30). Approaching natural early-stop threshold (10 consecutive no-improve epochs confirmed).

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0074 (有效, above baseline)
  - vs champion (posA_l1=0.5012): γ = -0.0044 (不及 champion)
  - vs M17-ORT (orth_weight=0.01, Best=0.5005): γ = -0.0037
  - vs D1-detail (0.5003): γ = -0.0035
  - vs M32-DRP (Delete Routing Path, running 0.4998@ep16): γ = -0.0030
  - DTW is in the mid-tier group (~0.495-0.499), adding density weights to cluster readback provides +0.0074 vs baseline but underperforms simpler additive variants (posA_l1 0.5012, ORT 0.5005).

## 5. Conclusion
  - 结论: [持平] — density-weighted token injection improves over baseline (+0.0074) but does NOT exceed champion or other single mechanisms.
  - 解释: Weighting cluster tokens by point density (log-count normalized) degrades vs uniform readback (posA_l1 0.5012). The density prior may introduce bias toward larger clusters (background), diluting the signal from smaller-but-important clusters (object boundaries). This is consistent with the pattern that ALL additive injection variants cluster around 0.495-0.501, suggesting the injection PARADIGM (not the weighting scheme) is the bottleneck.
  - 对后续实验设计的建议: 
    (a) Confirms additive injection variants cannot break the ~0.5005 ceiling — focus on non-additive paradigms (FiLM/M38 already in queue)
    (b) Density prior hypothesis: larger clusters dominate → smaller clusters underserve — could try inverse-density weighting
    (c) Close density-weighting direction; do not design more DTW variants.
    (d) Process disappearance at epoch 30 (natural convergence already occurred) — 10 consecutive no-improve epochs from ep21-30 would have auto-early-stopped. Result is reliable.

## 6. Crash Info (if crashed)
  - Error type: stopped_unknown (silent process death)
  - Error message excerpt: N/A — process disappeared after epoch 30. No error signature in log. 10 consecutive no-improve epochs verified; experiment was near natural termination.
  - Auto-fix attempt: N/A — experiment converged before process death. Reliable result.
================================================================================
