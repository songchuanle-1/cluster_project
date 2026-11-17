# Experiment Result Analysis — cluster_project

## 1. Basic Info
- ID: M226-WFC; server-4 physical GPU0; source94.
- State: done_earlystop; native epoch30/50. The original resumed process is absent.
- Native stop: 2026-11-04 19:39:40.758 server log time (Asia/Shanghai).
- Canonical archive: ead6b5a9edf2466ea96e2587c931c865; original archive time and history retained.

## 2. Best Metrics
| Metric | Value | Epoch |
|---|---|---|
| mIoU, complete experiment best | 0.49711745977401733 | Restored history; exact best epoch not re-established here |
| Last validation mIoU | 0.48382365703582764 | 30 |
| Acc@50 at best | Unknown in this resumed log | Unknown |
| spmIoU at best | Unknown in this resumed log | Unknown |

## 3. Convergence Summary
Restored epoch25/best=0.49711745977401733/no-improve5; resumed epochs26–30 produced [0.48364129662513733, 0.48184701800346375, 0.48421984910964966, 0.4811730682849884, 0.48382365703582764].
No validation exceeded the restored best. The exact lineage reaches no-improve10,
and stdout plus native logger both record the original patience10 stop at epoch30.
The native break precedes checkpoint saving, so last.pth may remain epoch29;
its recorded SHA is evidence of preserved bytes, not a CPU inspection of its body.

## 4. Comparison
Against baseline .4894: +0.0077174598. Against champion M95 .5020:
-0.0048825402. Target .5100 remains unmet; champion remains unchanged.

## 5. Interpretation
This complete experiment did not improve the champion. This observation does
not establish a hypothesis-wide failure or justify tuning, restart or migration.
Generic archival recorded .4840 from rounded resumed-only stdout and an empty
local-log path; a separate evidence-backed correction retains that original history.

## 6. Next Action
Preserve source, checkpoints, admissions and original pause/resume lineage.
Continue existing independent NEC/MIC candidates under GPU0-only authorization.
Evidence: [{'path': 'pipeline/diagnostic_bundles/tick_f77b26d6/wfc_terminal_observation.json', 'sha256': '61f616ff5ee556056d0c266731d0cbae460c2d732b803f7482fe8f7b1e24bd0c'}, {'path': 'pipeline/diagnostic_bundles/tick_f77b26d6/wfc_terminal_independent_review.json', 'sha256': 'a49452a3d584fa22ca7d4a99c69ea542a9f4e1a701c68e927308b38eb44c4c39'}, {'path': 'pipeline/diagnostic_bundles/tick_f77b26d6/native_logger_terminal_full.log', 'sha256': 'a5dffadd0d63a66aee295449ee984f3ef615000bd14ffba822d9dd7dc198e5d6'}, {'path': 'pipeline/diagnostic_bundles/tick_f77b26d6/stdout_terminal_full.log', 'sha256': 'ac3477d400bf01b14bc85032f5af5289f0c1b8811771f656bed2dd891eb5a61e'}, {'path': 'pipeline/diagnostic_bundles/tick_f77b26d6/wfc_canonical_reconcile_confirmed.json', 'sha256': '87a8f9e9d634a5115066747fc162c771bb4d5f556465d37d7865de0fcb8cf95c'}]
