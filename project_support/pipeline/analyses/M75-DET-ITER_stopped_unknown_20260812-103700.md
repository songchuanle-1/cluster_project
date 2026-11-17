================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M75-DET-ITER | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M75-DET-ITER
  - Config: configs/Quard/det_iter/model_base1_quard2_c2f_enc_lite_posA_l1_det_iter.yaml
  - Server: server-6 | GPU: 7
  - Started: ~2026-08-09 | Finished: 2026-08-12 10:13:58 | Duration: ~3d
  - State: stopped_unknown (process interrupted before early-stop criterion)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4956 | ≤20     |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch ≤20
  - Final epoch: 20/50, interrupted mid-training
  - Replaced by new tasks (qmod/mlay/qmod_mlay) on server-6 GPU7

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0062 (modest gain)
  - vs champion (0.5012): γ = -0.0056 (not breaking through)
  - vs M69-ITER (0.4978): γ = -0.0022 (detail message + iter: no positive synergy)

## 5. Conclusion
  - Conclusion: [FAIL] below champion, iter x detail negative interaction
  - Explanation: detail message x iter readback (0.4956) < ITER alone (0.4978), detail and iter mechanisms conflict; iter branch also shows M77-ITER-HCG (0.4933) < ITER alone
  - Recommendation: close iter branch, focus on CTF and HCG axes

## 6. Crash Info (stopped_unknown)
  - Error type: process preempted (server-6 GPU7 reassigned to new tasks)
  - Note: not a crash; best recorded, training incomplete
================================================================================
