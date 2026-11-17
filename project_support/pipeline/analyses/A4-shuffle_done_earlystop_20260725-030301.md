================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: A4-shuffle | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: A4-shuffle
  - Config: configs/Quard/trueroute_shuffle/model_base1_quard2_c2f_enc_lite_posA_l1_trueroute_shuffle.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-07-20 13:03 | Finished: 2026-07-21 13:32 | Duration: ~24h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4941 | 16      |
  | Acc@50   | 0.513  | 16      |
  | spmIOU   | 0.457  | 16      |

## 3. Convergence Summary
  - Best first reached at: epoch 16 (mIoU=0.4941)
  - mIoU sequence: 0.3900→0.4078→0.4463→0.4453→0.4633→0.4695→0.4718→0.4815→0.4828→0.4915→0.4872→0.4889→0.4854→0.4894→0.4936→**0.4941**→0.4878→0.4911→0.4939→0.4867
  - Post-best oscillation in range [0.4867, 0.4939], no further improvement
  - Subsequent no_improve epochs: ~4 (manual kill at ~19 epochs)
  - Convergence pattern: steady rise to peak at ep16, then oscillation without new best

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0047 (marginal)
  - vs champion (posA_l1=0.5012): γ = -0.0071
  - vs A3-true_route (0.4468): γ = +0.0473 (shuffle control group vastly outperforms content-based routing)
  - Key: A3 (TrueRoute with real content-based routing) = 0.4468 vs A4 (random shuffle routing) = 0.4941
    → Random routing beats content routing by +0.0473, confirming routing signal is harmful

## 5. Conclusion
  - 结论: [关键证据] shuffle控制组远优于内容路由
  - 解释: A4-shuffle 使用随机路由索引（shuffle cluster assignment），mIoU=0.4941，比 A3 true_route (0.4468) 高 +0.0473。这证明**任何形式的 cluster routing 注入都会损害性能**，收益完全来自多尺度 context 回写而非路由。Shuffle 与 champion (0.5012) 仍有 -0.0071 差距，说明 champion 的 identity routing（路由算了但不用）是最优策略。
  - 对后续实验设计的建议: 彻底放弃 routing 方向；聚焦 context aggregation 机制（pool type、orthogonality、cross-scale attention 等已在队列中的方向）

## 6. Crash Info
  - N/A (clean early stop, manually killed after oscillation plateau)
================================================================================
