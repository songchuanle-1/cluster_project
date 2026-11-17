================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M90-CTF-HCG-S3 | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M90-CTF-HCG-S3
  - Config: configs/Quard/ctf_hcg_s3/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_s123.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-14 03:14 (log train_..._ctf_hcg_s123_20260814_031211.log) | Finished: 2026-08-14 20:07 | Duration: ~17h
  - State: done_earlystop (no_improve=11/10, 连续 11 epoch 未刷新 best, monitor kill PID=825216)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4940 | 25      |
  | Acc@50   | 0.547  | 25      |
  | spmIOU   | 0.458  | 25      |

## 3. Convergence Summary
  - Best first reached at: epoch 25
  - Subsequent no_improve epochs: 11 (killed at patience=10)
  - Trajectory: 前 17 epoch 单调上升 (0.42→0.45), ep17-25 爬升至 0.494 触顶, 此后验证在
    0.486-0.492 区间小幅回落震荡 (末 5: 0.4880/0.4880/0.4860), 未再刷新, 判定早停。
  - 与 M81 (seed 1999) 对比: 收敛形态相近但峰值低 0.0072。

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0046 (有效)
  - vs current champion (posA_l1 0.5012): γ = -0.0072 (未破顶)
  - vs M81-CTF-HCG (0.5012, stopped_unknown ep31, seed 1999): γ = -0.0072 — **同一 CTF×HCG
    配置换 seed=123 掉点明显**, 复现性存疑
  - vs M65-HCG (0.5002, seed 1999): γ = -0.0062
  - vs M91-HCG-R2 (HCG alone seed=42, running 0.4960@ep24): 同 seed=42 系, 待终态

## 5. Conclusion
  - 结论: [有效] (优于 baseline +0.0046) 但 [未破顶] 且复现性存疑
  - 解释: M90 是 CTF×HCG champion-tie (M81=0.5012) 的 seed=123 复现检查, 结果 0.4940
    低于 M81 达 0.0072。说明 0.5012 的"champion-tie"可能含 seed=1999 的有利性, 而非
    机制本身的稳定增益。CTF×HCG 的真实水平可能落在 0.494-0.501 区间。
  - 对后续实验设计的建议: 等 M89-CTF-HCG-R2 (seed=42) 与 M91-HCG-R2 (seed=42) 终态
    确认复现区间; 若 seed=42 同样 <0.50, CTF×HCG 轴降级为"部分有效"而非"破顶方向",
    已入队的 M92-ORT/M95-CSORT/M96-2LAY 组合实验结果需按此基准重解释。
================================================================================
