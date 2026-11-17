# Experiment Result Analysis - cluster_project
Experiment M196-CTF-HCG-CSORT-BCA; registry done_earlystop.

## 1. Basic Info
- Config: configs/Quard/ctf_hcg_csort_bca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bca.yaml
- Server4 GPU0,PID3237667;started2026-09-14 22:52:42;monitor kill2026-09-16 07:01:13.
- Native PID absent at manual verification. Logger last train epoch23 step260;
  stdout last observed step268. No automatic restart.
- Registry reports .4800 and23/50;23 is partial training,not completed validation.

## 2. Best Metrics
| Metric | Value | Epoch |
|---|---|---|
| mIoU |.47992366552352905|17|
| Acc50 |.534|17|
| spmIoU |.438|17|
| spAcc50 |.489|17|
Exact native logger22validation records;lastVAL22 .465435266494751.

## 3. Convergence Summary
Five validation records follow peak17,not11. Last sequence:
.4799236655,.4736389816,.4729035199,.4752729833,.4742989838,.4654352665.
Decision070113 says no_improve11>=10. Rounded stdout independently has22values,
peak.480 at17,also5subsequent validations. Precision alone does not explain11.
Current source parse_running_miou should return5 for either supplied stream.
Actual executable/lineage provenance of kill remains unresolved.

## 4. Comparison
Against exact baseline .4894491136:delta-.0095254481.
Against exact M95 .5024607182:delta-.0225370526.
Observed belowbaseline/champion;not evidence of a completed patience10 screen.

## 5. Conclusion
Observed performance unsuccessful throughVAL22;do not extend BCA or tune it.
Do not infer theoretical mechanism failure from this prematurely terminated
or misreported screen. Audit stopping provenance;preserve checkpoint and no restart.

## 6. Termination Evidence
Native log: pipeline/reports/M196_native_terminal_20260916.log
SHA256:c2c52010045449586a3951560927989d7051e3917446fdee24d259e5df61cb87.
Decision:pipeline/decisions/20260916-070113_early_stop.md.
Question:pipeline/decisions/20260916-070627_question.md.
