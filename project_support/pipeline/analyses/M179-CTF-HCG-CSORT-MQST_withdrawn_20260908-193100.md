================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M179-CTF-HCG-CSORT-MQST | State: withdrawn
================================================================================

## 1. Basic Info
- Config: configs/Quard/ctf_hcg_csort_mqst/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqst.yaml
- Planned server: server-4 | GPU: unassigned
- Training start/end/duration: N/A; never launched.
- Disposition: withdrawn for measured resource noncompliance, not crashed.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | N/A | N/A |
| Acc@50 | N/A | N/A |
| spmIOU | N/A | N/A |
Full-model profile:10.178109868G,157616186 parameters,893.871MiB.
Median/P90:127.249/177.471ms; bs1/warmup20/repeat100, RTX5090 with shared load.
Source: reports/mq_resource_audit_20260908-1912/resource_audit.json.

## 3. Convergence Summary
No training or convergence evidence. The resource audit ran inference only.

## 4. Comparison
- M95 profile9.762532428G; original subtree graph exceeds10G by0.178109868G.
- Training mIoU differences are unavailable; do not infer mechanism failure.

## 5. Conclusion
- Resource-ineligible original graph withdrawn. Code/config retained.
- New isolated M184-MQST-TR removes intermediate context feedback and passes
 9.845647916G; this is a new experiment, not a rewrite or rerun of M179.
- Old subtree method also assumes equal batch cluster counts; the new package
  fixes this under padding regression tests. The original remains unchanged.

## 6. Crash Info (if crashed)
No training crash; original unstarted, new-package pre-enqueue test repaired once.
Decisions:191559_route_change and193039_next_batch. No fabricated ledger score.
================================================================================
