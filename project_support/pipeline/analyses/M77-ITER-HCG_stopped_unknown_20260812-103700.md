================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M77-ITER-HCG | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M77-ITER-HCG
  - Config: configs/Quard/iter_hcg/model_base1_quard2_c2f_enc_lite_posA_l1_iter_hcg.yaml
  - Server: server-6 | GPU: 7
  - Started: ~2026-08-09 | Finished: 2026-08-12 10:14:03 | Duration: ~3d
  - State: stopped_unknown (process interrupted before early-stop criterion)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4933 | ≤20     |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch ≤20
  - Final epoch: 20/50, interrupted mid-training
  - Replaced by new tasks on server-6 GPU7

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0039 (modest gain)
  - vs champion (0.5012): γ = -0.0079 (far from champion)
  - vs M69-ITER (0.4978): γ = -0.0045 (HCG hurts ITER performance)
  - vs M65-HCG (0.5002): γ = -0.0069 (ITER degrades HCG delivery quality)

## 5. Conclusion
  - Conclusion: [FAIL] iter x HCG negative interaction
  - Explanation: ITER (iterative readback) + HCG (correct multi-scale delivery) = 0.4933, lower than both independent axes; the two mechanisms mutually interfere; iterative readback disrupts HCGs delivery path
  - Recommendation: close iter branch; keep HCG standalone; focus on CTF+HCG combination

## 6. Crash Info (stopped_unknown)
  - Error type: process preempted (server-6 GPU7 reassigned)
  - Note: not a crash; best recorded
================================================================================
