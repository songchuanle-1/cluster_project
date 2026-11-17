# M199-BEI Native Terminal Analysis

## 1. Basic Info
server-6 GPU7; PID630864 absent at live reconciliation.
Original logger ended at 2026-10-11 15:02:50,542 in its own clock.
Local reconciliation: 2026-10-11 23:21:05+08:00.
Checkpoint retained remotely. Exact native log archived with remote/local
SHA256 4c23a2fe5d3667ab80334fe0875d166a17e2b12450f0cde82d28b9aee6370ed7.
Source and parser: pipeline/reports/terminal_facts_20261011.json and
scripts/reconcile_terminals_20261011.py.

## 2. Best Metrics
| Metric | Value | Epoch |
|---|---|---|
| mIoU | 0.4741974174976349 | 16 |
| Acc@50 | 0.534 | 16 |
| spmIOU | 0.435 | 16 |
Acc@50 and spmIOU are paired rounded logger values.

## 3. Convergence Summary
Verified one validation for every epoch1..26. Trainer explicitly stopped
after ten validations without improvement. Final mIoU0.4577920138835907,
Acc@500.516, spmIOU0.415. Separate frozen convergence/subgroup criteria have
not been established from this terminal summary.

## 4. Comparison
Best is -0.0152025825023651 below rounded baseline0.4894,
-0.0278025825023651 below rounded champion0.5020, and below target0.5100.
These single-seed aggregate differences are not scene-clustered uncertainty
or causal mechanism estimates.

## 5. Conclusion
The trained directed boundary-incidence realization did not improve M95.
Do not promote, tune, automatically restart or rename this realization.
Inference resource PASS did not establish efficacy.

## 6. Crash Info
No crash evidence: explicit native early-stop line and absent recorded PID.
Corrected stale running state to done_earlystop; removed only this owned slot
and queue entry and appended exactly one terminal CSV row. Training launch
history and all earlier repeat failures remain intact.
