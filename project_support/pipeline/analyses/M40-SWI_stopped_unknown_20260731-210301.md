================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M40-SWI | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M40-SWI
  - Config: configs/Quard/swi/model_base1_quard2_c2f_enc_lite_posA_l1_swi.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-07-30 14:03:38 | Finished: 2026-07-31 21:08:53 | Duration: ~31h
  - State: stopped_unknown (process silently disappeared during epoch 20 training, iter ~2310/4686)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4970 | 14      |
  | Acc@50   | 0.540  | 14      |
  | spmIOU   | 0.453  | ~14     |

## 3. Convergence Summary
  - Best first reached at: epoch 14 (2026-07-31 17:46)
  - Subsequent no_improve epochs: 5 (epochs 15-19)
  - Final epoch best: mIoU=0.4970 vs historical best=0.4970
  - 序列: 0.337→0.385→0.402→0.413→0.430→0.444→0.460→0.468→0.479→0.479→0.483→0.492→0.489→**0.497**→0.491→0.488→0.495→0.493→0.489
  - 收敛形态: 前13 epoch 持续快速上升，epoch 14 触顶 0.4970，之后 5 个 epoch 在 0.488-0.495 震荡未恢复。若继续运行预计 epoch ~24 触发 early-stop。崩溃时 no_improve=5/10。

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0076 (有效)
  - vs champion (model_base1_quard2_c2f_enc_lite_posA_l1 0.5012): γ = -0.0042 (未超越)
  - vs M41-CTF (done_earlystop 0.4995): γ = -0.0025 (SWI < CTF)
  - vs M32-DRP (stopped_unknown 0.5012): γ = -0.0042

## 5. Conclusion
  - 结论: [有效但有限] — 超越 baseline (+0.0076)，距 champion 较远 (-0.0042)
  - 解释: Sigmoid-Weighted Injection (per-scale independent sigmoid gate 替代 softmax competitive fusion) 改进了多尺度融合方式，收益存在但有限。独立 sigmoid 让各尺度自己决定贡献比例，优于 softmax 的竞争性分配，但未能显著突破性能天花板。与 CTF (token 质量方向) 相比略逊 (-0.0025)，说明当前瓶颈更可能在 token 表示质量而非融合权重分配。
  - 对后续实验设计的建议: Sigmoid gate 方向收益有限(0.4970)，不推荐继续深挖。等待队列中 M42-WCA (加权聚合) / M43-CLN (token normalization) / M44-CSF (跨尺度融合) 结果，继续探索不同维度瓶颈。

## 6. Crash Info
  - Error type: Silent process death (no error in training log, no OOM kill in dmesg)
  - Error message excerpt: Last log line at 21:08:53 shows normal training (epoch 20 iter 2310, loss=0.3244, grad=1.99). Process disappeared within seconds after.
  - NOTE: 6 zombie SWI sibling processes (pids 1852389/1852440/1852441/1852444/2814339/2814387) were killed at ~21:03. Active pid 1849933 was NOT in kill list but also disappeared. Cause uncertain — possibly system resource pressure from zombie processes.
  - Auto-fix attempt: N/A (not a code bug, process death from unknown system cause)
================================================================================
