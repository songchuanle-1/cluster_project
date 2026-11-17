================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M182-CTF-HCG-CSORT-MQFC | State: withdrawn
================================================================================

## 1. Basic Info
- Config: configs/Quard/ctf_hcg_csort_mqfc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqfc.yaml
- Planned server: server-4 | GPU: unassigned
- Training start/end/duration: N/A; never launched.
- State: withdrawn for resource noncompliance.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | N/A | N/A |
| Acc@50 | N/A | N/A |
| spmIOU | N/A | N/A |
Full-model10.167296428G,157616186 parameters,893.871MiB.
Median/P90:184.354/280.353ms; bs1/warmup20/repeat100, shared RTX5090.
Source: reports/mq_resource_audit_20260908-1912/resource_audit.json.

## 3. Convergence Summary
No training or validation outcome. Higher measured latency is observational;
shared load prevents a causal speed claim.

## 4. Comparison
M959.762532428G; frontier graph exceeds10G by0.167296428G.
No mIoU comparison. fvcore omits listed unsupported operations.

## 5. Conclusion
Withdraw recurrent frontier candidate, preserve original code/config.
M187-MQFC-TR independently removes intermediate feedback and reads frontier
context at final prediction; measured9.843485228G. No arbitrary top-k/depth sweep.
Inherited unequal-cluster handling is repaired only in the new package.

## 6. Crash Info (if crashed)
No training crash. Replacement padding repair1 passed focused CUDA tests.
Decisions191559/193039; do not add an accuracy score for an untrained model.
================================================================================
