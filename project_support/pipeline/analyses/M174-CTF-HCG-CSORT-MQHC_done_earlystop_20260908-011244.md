================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M174-CTF-HCG-CSORT-MQHC | State: done_earlystop
================================================================================

## 1. Basic Info
- ID: M174-CTF-HCG-CSORT-MQHC
- Config: configs/Quard/ctf_hcg_csort_mqhc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqhc.yaml
- Server: server-4 | GPU: 0
- Started: 2026-09-07 09:44:09 | Finished: 2026-09-08 01:07:44
- Duration: 15h 23m 35s | State: done_earlystop
- Stopped during epoch 23; last completed evaluation was epoch 22.
- Recovered source: Checkpoints/server-4/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqhc/20260907_094408/20260907_094408.log

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | 0.4934916496 | 17 |
| Acc@50 | 0.548 (rounded log) | 17 |
| spmIOU | 0.457 (rounded log) | 17 |
The registry retains the monitor's rounded 0.4930; the recovered precise best rounds to 0.4935.

## 3. Convergence Summary
- Best first reached at epoch 17. Completed evaluations 18-22: 0.48914772, 0.49044627, 0.49049178, 0.49302799, 0.49053207.
- Five genuine post-best evaluations, not eleven. The monitor fallback regex also matched spmIOU, contaminating the sequence and triggering early stop before ten genuine evaluations.
- Final completed evaluation: 0.49053207 versus historical best 0.49349165.
- This is a partial-patience run. Do not interpret it as a completed full-patience convergence test.

## 4. Comparison
- vs baseline model_base1=0.4894: +0.00409165.
- vs M169 hierarchy branch=0.5000: -0.00650835.
- vs champion M95=0.5020: -0.00850835.
- Other historical fallback-parsed runs may share the early-stop bias; comparisons are descriptive, not causal proof.

## 5. Conclusion
- Conclusion: positive versus baseline, below champion, with compromised stopping evidence.
- Soft minimum-occupancy consensus did not surpass the hard hierarchy branch within the observed training window. This does not establish that a full-patience run would fail.
- Preserve the remote checkpoint; do not expand this mechanism based on the present evidence. Retain M177 and the existing topology queue.
- Retrospective resume/rerun policy is logged in decisions/20260908-011223_question.md.

## 6. Crash Info (if crashed)
- No model crash. Monitor-induced early stop with a parser defect.
- Parser repair attempt 1: exclude spmIOU via token boundary; two regression tests passed and remote read-only monitoring verified corrected counts.
================================================================================
