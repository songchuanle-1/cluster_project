# Experiment Result Analysis - cluster_project
Experiment: M192-CTF-HCG-CSORT-MQHF-TR | State: withdrawn_resource

## 1. Basic Info
- Config: configs/Quard/ctf_hcg_csort_mqhf_tr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqhf_tr.yaml
- Server: server-4 GPU1 for bounded admission only; never enqueued or trained.
- Created13:17; measured13:20-13:21 Sep10. Rejected13:22:46.
- Commit897e761efe09a325c66dab24e7c50806f103ab96, synchronized both servers.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | N/A, never trained | N/A |
| Acc@50 | N/A | N/A |
| spmIOU | N/A | N/A |
Resource:10.045073964G;157616186params;893.87109375MiB inference allocated;
median172.1206ms/P90270.8419ms, bs1/warmup20/repeat100.

## 3. Convergence Summary
No training or convergence. CUDA scalar oracle, zero-flow ties, mask switch,
input gradients, padding exclusion/isolation, exact boundary, own resolver and
full decoder backward passed. Full-model output finite.

## 4. Comparison
- FLOPs limit10G exceeded by .045073964G. Hard gate, not rounding tolerance.
- Matched M95=9.762532428G;893.3671875MiB;170.5414/258.4630ms.
- Inference allocation increase<15%, but FLOPs failure alone blocks admission.
- One scene/description, sharedGPU1, unsupported fvcore operators recorded.
  No training-memory bound or timing advantage claimed.

## 5. Conclusion
- Resource-ineligible; preserve evidence and independent code, do not enqueue.
- No numeric rescue, formula adjustment, or claim that the mechanism failed
  on accuracy. No efficacy ledger row because there was no training.
- Evidence: reports/flow_validation_20260910-1316/resource_audit.json;
  *_tests.json; decision20260910-132246_route_change.md.

## 6. Crash Info (if crashed)
- Not a crash; model repair attempts0. Resource rejection does not use retries.
