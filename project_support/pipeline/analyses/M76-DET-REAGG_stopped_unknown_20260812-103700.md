================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M76-DET-REAGG | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M76-DET-REAGG
  - Config: configs/Quard/det_reag/model_base1_quard2_c2f_enc_lite_posA_l1_det_reag.yaml
  - Server: server-6 | GPU: 7
  - Started: ~2026-08-09 | Finished: 2026-08-12 10:14:00 | Duration: ~3d
  - State: stopped_unknown (process interrupted before early-stop criterion)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4909 | ≤20     |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch ≤20
  - Final epoch: 20/50, interrupted mid-training
  - Replaced by new tasks on server-6 GPU7

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0015 (below 0.002 threshold)
  - vs champion (0.5012): γ = -0.0103 (far below champion)
  - vs M70-REAGG (0.4983): γ = -0.0074 (detail message conflicts with reaggregate)

## 5. Conclusion
  - Conclusion: [FAIL] detail x reaggregate strongly negative
  - Explanation: detail x reaggregate (0.4909) far below REAGG alone (0.4983); detail message conflicts with cluster re-aggregation mechanism; REAGG axis has multiple negative signals (M79=0.4919 fix regression, M76=0.4909 detail conflict)
  - Recommendation: abandon REAGG axis entirely; focus on CTF + HCG combination

## 6. Crash Info (stopped_unknown)
  - Error type: process preempted (server-6 GPU7 reassigned)
  - Note: not a crash; best recorded
================================================================================
