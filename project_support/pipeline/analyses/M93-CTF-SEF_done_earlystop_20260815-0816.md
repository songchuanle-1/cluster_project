================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M93-CTF-SEF | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M93-CTF-SEF
  - Config: configs/Quard/ctf_sef/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_sef.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-14 21:21 (launched after Phase 3b fix, crash recovered) | Finished: 2026-08-15 08:07
  - State: done_earlystop (no_improve=11/10, monitor kill PID=3382141; 首次 kill 07:16 PID=3381263 后重启)
  - Note: 08-14 21:21 bugfix (841f883) 修复 "Unknown cluster_mode: ctf_sef" 启动 crash 后重推。

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4910 | 18      |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (Acc50/spmIOU 未拉取: 日志拉取失败, checkpoint 留远端)

## 3. Convergence Summary
  - Best first reached at: epoch 18 (mIoU 0.4910)
  - Subsequent no_improve epochs: 11 (killed at patience=10)
  - Final trajectory: 验证序列 0.4430, 0.4900, 0.4560, 0.4860, 0.4510 — 高振幅震荡,
    触顶 0.4910 后未再刷新, 判定早停。
  - 07:16 首次 kill 后进程重启 (PID 3381263→3382141), 08:07 二次 kill 终态。

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0016 (勉强高于 baseline, 实质持平)
  - vs current champion (posA_l1 0.5012): γ = -0.0102 (未破顶, 显著低于)
  - vs M41-CTF (0.4995): γ = -0.0085 — SEF 加在 CTF 上反降 0.0085
  - vs M84-DET-CTF-HCG (0.4990): 同量级 detail/SEF 附加机制均无正增益

## 5. Conclusion
  - 结论: [失败] (相对 champion 掉点 0.0102, 相对 CTF 单独掉点 0.0085)
  - 解释: SEF (Squeeze-and-Excitation channel attention on cluster tokens) 作为
    CTF 的附加通道注意力, 与门控/缩放系机制 (banned 的 gate 族) 同族 — 通道级
    scaling 改变数值分布而非信息流路径, 符合 Phase 1.6 调参气味信号 #3。实验
    证伪 "SE 通道注意力提升 cluster token 表达" 假设。
  - 对后续实验设计的建议: SEF/gate 族不再投入 (与 cag/cfe/layerscale 三连败
    合并为 gate 系禁区证据 +1)。CTF×HCG 组合轴与多样性轴 (ORT/CSORT) 继续。
================================================================================
