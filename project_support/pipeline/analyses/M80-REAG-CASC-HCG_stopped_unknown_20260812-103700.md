================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M80-REAG-CASC-HCG | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M80-REAG-CASC-HCG
  - Config: configs/Quard/reag_casc_hcg/model_base1_quard2_c2f_enc_lite_posA_l1_reag_casc_hcg.yaml
  - Server: server-4 | GPU: —
  - Started: ~2026-08-10 | Finished: 2026-08-12 09:00:28 | Duration: ~2d
  - State: stopped_unknown (process interrupted, 30/50 epochs completed)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4965 | ≤30     |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch ≤30
  - 30/50 epochs completed before interruption

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0071 (effective)
  - vs champion (0.5012): γ = -0.0047 (not breaking through)
  - vs M78-REAGG-HCG (0.5008): γ = -0.0043 (cascade-fixed version worse than simple)
  - vs M79-REAG-CASC (0.4919): γ = +0.0046 (HCG still adds value, but cascade reaggregate is weak)

## 5. Conclusion
  - Conclusion: [FAIL] cascade fix direction yields no positive gain
  - Explanation: M79 single-variable control already proved cascade fix regression (-0.0064 vs M70); adding HCG only recovers to 0.4965, still below M78 (REAGG+HCG=0.5008); the problem is in reaggregate mechanism itself, not HCG delivery
  - Recommendation: abandon entire REAGG axis; focus HCG pairing with CTF and QMOD

## 6. Crash Info (stopped_unknown)
  - Error type: process preempted (server-4 rescheduled)
  - Note: not a crash; best recorded
================================================================================
