================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M180-CTF-HCG-CSORT-MQPP | State: withdrawn
================================================================================

## 1. Basic Info
- Config: configs/Quard/ctf_hcg_csort_mqpp/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqpp.yaml
- Planned server: server-4 | GPU: unassigned
- Training start/end/duration: N/A; never launched.
- State: withdrawn for resource noncompliance, not a training crash.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | N/A | N/A |
| Acc@50 | N/A | N/A |
| spmIOU | N/A | N/A |
Full-model10.179092908G,157616186 parameters,893.871MiB.
Median/P90:126.174/189.187ms; bs1/warmup20/repeat100, shared RTX5090.
Source: reports/mq_resource_audit_20260908-1912/resource_audit.json.

## 3. Convergence Summary
No training validation or convergence series exists.

## 4. Comparison
M959.762532428G; original path posterior exceeds10G by0.179092908G.
No training accuracy comparison is possible.

## 5. Conclusion
Withdraw the resource-ineligible recurrent graph, preserve original code.
M185-MQPP-TR independently tests posterior context at terminal readout,
measured9.845844524G. No claim that a failed training result was improved.
New package also corrects inherited padded-cluster indexing.

## 6. Crash Info (if crashed)
No training crash. Shared pre-enqueue padding repair1 applies to new package.
Decisions191559/193039; no fake accuracy row added to experiments.csv.
================================================================================
