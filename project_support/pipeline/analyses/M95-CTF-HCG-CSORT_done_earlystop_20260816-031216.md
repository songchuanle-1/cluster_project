================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M95-CTF-HCG-CSORT | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M95-CTF-HCG-CSORT
  - Config: configs/Quard/ctf_hcg_csort/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-15 10:10:12 (relaunch; 首启 08:16:31 于 gpu0 crash, Phase 3b 修复后重入队)
  - Finished: 2026-08-16 03:07:24 | Duration: ~17h
  - State: done_earlystop (no_improve=11/10 ≥ patience=10, monitor kill PID=949721)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5020 | 16/22   |
  | Acc@50   | 0.557  | 16/22   |
  | spmIOU   | 0.465  | 16/22   |
  (序列: 0.247, 0.379, 0.408, 0.431, 0.448, 0.462, 0.475, 0.472, 0.485, 0.486,
          0.487, 0.492, 0.495, 0.490, 0.498, 0.502, 0.497, 0.493, 0.495, 0.499, 0.498)

## 3. Convergence Summary
  - Best first reached at: epoch 16 (relaunch 后第 16 次验证, 总进度 22/50)
  - Subsequent no_improve epochs: 5 (ep17-21 均未刷新, 但早停判定聚合历史日志 no_improve=11/10)
  - Final epoch best: mIoU=0.4980 vs historical best=0.5020
  - 收敛形态: 快速上升 (ep1-6: 0.247→0.462) → 缓慢爬升且震荡 (ep7-16: 0.475→0.502,
    期间三次回踩 <0.49) → 平台 (ep16 后 5 轮未刷新)

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0126 (有效, context 机制核心收益保留)
  - vs 前 champion (A1 posA_l1=0.5012 / M81-CTF-HCG=0.5012): γ = +0.0008 (首个 >champion 观测)
  - vs ORT 族: M92-CTF-HCG-ORT=0.4930, M94-HCG-ORT=0.4930 → CSORT +0.009 vs ORT,
    跨尺度正交 (csort) 优于尺度内正交 (ort)
  - vs CTF×HCG seed 对照组: M89(s42)=0.4980, M90(s123)=0.4940 → M95(seed1999)=0.5020
    在已知 seed 方差区间 (±0.004~0.007) 内

## 5. Conclusion
  - 结论: [有效] — 首个 mIoU > champion 的观测 (0.5020 > 0.5012), CSORT 成为新破顶候选
  - 解释: CTF×HCG 基底上加跨尺度正交约束 (csort_weight=0.01) 刷出 0.5020, 比 ORT
    多 0.009, 说明跨尺度正交多样性比尺度内正交更契合 cluster context 回写机制
  - 对后续实验设计的建议: **必须跨 seed 验证才能判定机制真伪** — +0.0008 在 seed
    方差内, 可能是 seed1999 有利性。已入队 M103(CSORT s2026, 对照 M102 CTF×HCG s2026)
    + M104(CSORT s42, 对照 M89 CTF×HCG s42=0.4980), 用同 seed 对照剥离方差。
    若同 seed 增量一致为正 → CSORT 成立为破顶方向; 若无 → 0.5020 归因 seed1999。

## 6. Crash Info (if crashed)
  - 首启 (2026-08-15 08:16 gpu0) crash:
    - Error type: IndexError (dimension mismatch)
    - Error message excerpt:
      ```
      File ".../ctf_hcg_csort/hier_postprocess.py", line 669, in _cross_scale_orth_loss
        agg[b, p] = fine_tokens[b, children].mean(dim=0)
      IndexError: index 177 is out of bounds for dimension 1 with size 64
      ```
  - Auto-fix: Y — Phase 3b (commit d319014 "cross-scale map inverse"), 修复后重入队 gpu1 启动
  - 重试: 第 1 次, 结果: fixed (relaunch 完整收敛至早停)
================================================================================
