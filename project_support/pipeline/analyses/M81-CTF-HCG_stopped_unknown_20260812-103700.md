================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M81-CTF-HCG | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M81-CTF-HCG
  - Config: configs/Quard/ctf_hcg/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg.yaml
  - Server: server-4 | GPU: —
  - Started: ~2026-08-11 11:27 | Finished: 2026-08-12 09:26:57 | Duration: ~22h
  - State: stopped_unknown (process interrupted, 31/50 epochs completed)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5012 | ≤31     |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch ≤31
  - 31/50 epochs completed; already at champion-tie level when interrupted
  - Potential for further improvement with more epochs

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0118 (strongly effective)
  - vs champion (0.5012): γ = +0.0000 (TIES CHAMPION! first stopped_unknown to reach this)
  - vs M41-CTF alone (0.4995): γ = +0.0017 (HCG adds positive contribution to CTF)
  - vs M65-HCG alone (0.5002): γ = +0.0010 (CTF adds positive contribution to HCG)

## 5. Conclusion
  - Conclusion: [EFFECTIVE] Ties champion!
  - Explanation: CTF (token FFN refinement) x HCG (correct multi-scale delivery) = 0.5012, first positive synergy between two independent effective axes (CTF +0.0101 vs baseline, HCG +0.0108 vs baseline, combo +0.0118). The two directions improve token quality and message delivery respectively, non-conflicting mechanisms.
  - Recommendation: STAR experiment — CTF x HCG is the most promising direction combination:
    (a) Re-run M81-CTF-HCG with full 50 epochs to confirm reproducibility and check for higher peak
    (b) Test CTF x HCG + QMOD (query modulation) or + MLAY (multi-layer injection) to break through
    (c) CTF x HCG + detail message (M84 already in queue)

## 6. Crash Info (stopped_unknown)
  - Error type: process preempted (server-4 rescheduled; M82/M83 resume took slot)
  - Note: not a crash; this result (0.5012 = champion) is critically important for future design
================================================================================
