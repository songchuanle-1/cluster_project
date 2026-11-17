================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M197-PIRS | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M197-PIRS
  - Config: configs/Quard/pirs/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pirs.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-09-16 12:26:33 | Finished: 2026-09-20 09:48:31
  - State: stopped_unknown

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4920 ledger / 0.4924 observed peak | preterminal |
  | Acc@50   | not terminally established | — |
  | spmIOU   | not terminally established | — |

## 3. Convergence Summary
  - Last verified progress: epoch 27/50, step 3241/4686.
  - The remote log stopped at 2026-09-20 01:33:12 UTC.
  - No normal completion, early-stop, traceback, or CUDA OOM marker was found.
  - `last.pth` and `best.pth` remain on server-6; this is an interrupted run, not a completed efficacy result.

## 4. Comparison
  - vs baseline (model_base1 0.4894491): ledger delta = +0.00255.
  - vs champion (M95 0.5024607): ledger delta = -0.01046.
  - The comparison is descriptive only because M197 did not reach a valid terminal evaluation.

## 5. Conclusion
  - Conclusion: inconclusive interrupted run.
  - PIRS did not establish a metric improvement and remains prior-art engineering evidence rather than a new core mechanism.
  - Do not restart on server-6. Resume from the preserved `last.pth` only on verified server-4 GPU0/1 after checkpoint transfer and path adaptation checks.

## 6. Crash Info
  - Error type: process disappeared without an explicit error marker.
  - Error message excerpt: none present in the remote log tail.
  - Auto-fix attempt: N — migration policy disables server-6 dispatch; server-4 SSH is currently refusing connections.
================================================================================
