# M198-PDC Native Terminal Analysis

## 1. Basic Info
server-6 GPU7; PID225589 absent at live reconciliation.
Original native logger ended at 2026-10-11 12:50:39,991 in its own clock.
Local reconciliation: 2026-10-11 23:20:58+08:00.
Checkpoint retained remotely. Exact native log archived with remote/local
SHA256 6dfa270826813c3cb71bcc39368e6d20ea0b30a509f06718c2b5cf534edb7f60.
Source and parser: pipeline/reports/terminal_facts_20261011.json and
scripts/reconcile_terminals_20261011.py.

## 2. Best Metrics
| Metric | Value | Epoch |
|---|---|---|
| mIoU | 0.4977434277534485 | 15 |
| Acc@50 | 0.549 | 15 |
| spmIOU | 0.461 | 15 |
Acc@50 and spmIOU are paired rounded logger values.

## 3. Convergence Summary
Verified one validation for every epoch1..25. Trainer explicitly stopped
after ten validations without improvement. Final mIoU0.4843158423900604,
Acc@500.537, spmIOU0.445. Trainer patience is not proof of the separate
frozen last-five-mean convergence criterion.

## 4. Comparison
Best is +0.0083434277534485 above rounded baseline0.4894,
-0.0042565722465515 below rounded M95 champion0.5020, and below target0.5100.
Single-seed aggregate comparison is descriptive; scene uncertainty, subgroup
harm and full Pareto retention are not established by these logs.

## 5. Conclusion
This trained point-detail realization did not improve the champion.
Do not promote, tune or automatically restart it. Preserve original admission,
checkpoint, diagnostic failures and successful native controls.

## 6. Crash Info
No crash evidence: explicit native early-stop line and absent recorded PID.
Corrected stopped_unknown and fallback0.4980 to done_earlystop and exact best,
preserving previous experiment state/CSV row in history without duplicate row.
