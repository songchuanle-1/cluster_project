# Experiment Result Analysis — cluster_project

Experiment: M235-SINC | State: crashed | Archive: b75c9152d7fd4ecea9af538101d777d4

## 1. Basic Info
- Server4 physical GPU0; source b1e639b3ceb14bb5c65d9f81a084d41c834b951c.
- Canonical three-observation reconciliation archived the run at 2026-11-10 23:15:49 +08:00; PID2248650 absent in two additional direct samples.
- Canonical archive is unchanged. Its empty log_local is supplemented by a separately collected, remote/local SHA-verified 1938280-byte log under Checkpoints/server_4/M235-SINC/b75c9152d7fd4ecea9af538101d777d4/.

## 2. Best Metrics
| Metric | Value | Evidence scope |
|---|---|---|
| mIoU | 0.2790 | Canonical rounded log/archive value; no new exact metric claim |
| Prior exact saved mIoU | 0.2787637412548065 | Historical 13:13Z metadata observation at epoch1 |
| Fresh saved checkpoint epoch | 1 for best and last | ZIP/pickle scalar metadata; tensors/optimizer contents unverified |
| Acc@50 / spmIOU | UNKNOWN | Not newly measured |

## 3. Convergence Summary
- One complete saved epoch is established by metadata. The run ended during epoch2 at batch1870/4686, not after two complete epochs.
- No convergence, full training efficacy or resume-eligibility conclusion follows from this partial run.

## 4. Comparison
- Baseline/champion deltas are not an efficacy comparison because this training is incomplete. M95 champion remains unchanged.
- Technical native TRAIN2/resource admission remains historical evidence; it did not establish long-run stability.

## 5. Conclusion
- Runtime failure with implementation scope; the structural hypothesis and novelty remain unresolved.
- Preserve checkpoints, original admission and all failure evidence. No automatic restart, resume or consumed-entry replay.
- Closest prepared M236-CSO remains unmeasured natively; fresh GPU0 free10530MiB is below its original20000MiB startup budget. Overlay is permitted; no empty-card/context/utilization condition is imposed.

## 6. Crash Info (if crashed)
- tools/train.py130 optimizer.step() -> torch.optim.Adam.step/_init_group -> AttributeError: 'list' object has no attribute 'grad'.
- Fresh static diagnosis finds current installed Adam source/cache/header/bytecode/line mapping consistent. The reported line191 does not directly load .grad; this does not establish the exit-time code object or local optimizer objects. Root cause UNKNOWN.
- No Torch import, GPU computation, package/source repair, signals, restart or native retest was performed for the diagnosis. See pipeline/diagnostic_bundles/tick_91c85c42/m235_optimizer_source_diagnosis/diagnosis_summary.json.
