================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M134-DUAL | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M134-DUAL
  - Config: configs/Quard/ctf_hcg_dual/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_dual.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-25 13:11 | Finished: 2026-08-26 01:07 (早停 kill) | Duration: ~11.9h
  - State: done_earlystop (monitor kill PID=163627, no_improve=11/10 ≥ patience=10)
  - Cluster attention: ctf_hcg base (champion 结构), cluster_att_num_layers=1,
    decoder 经 qla(use_cluster_mem=True) + qia(use_cluster_mem_visual=True) 双通路
    共享 KV 直读多尺度 cluster tokens (DCM+DCMV 同时开启)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4970 | 21/50   |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (日志拉取失败, checkpoint 留远端; 指标来源 pipeline_monitor 日志尾解析)
  monitor 近5次验证序列: 0.4600, 0.4920, 0.4530, 0.4950, 0.4580 — Best 后震荡回落

## 3. Convergence Summary
  - Best first reached at: epoch 21 (mIoU=0.4970)
  - Subsequent no_improve epochs: 11/10 (monitor kill)
  - Final epoch best: mIoU=0.4970 (21/50) vs historical best=0.4970
  - 收敛形态: 快速上升后平台 (0.49-0.497), 与 ctf_hcg 系列同形态; 平台顶 0.4970
    低于 DCM 单通路 (M124=0.5010), 接近 DCMV 单通路 (M133=0.4950)

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = +0.0076 (有效, 仍过 baseline)
  - vs DCM qla 单通路 (M124-DCM = 0.5010): γ = -0.0040 — **双通路反而低于 qla 单通路**
  - vs DCMV qia 单通路 (M133-DCMV = 0.4950): γ = +0.0020 — 仅略高于 qia 单通路
  - vs current champion (M95-CTF-HCG-CSORT = 0.5020): γ = -0.0050
  - **{qla, qia}×{cluster KV} 2×2 矩阵补格完成**:
    - qla 单通路 (M124-DCM)   = 0.5010 ✓ (语言引导读路径最优)
    - qia 单通路 (M133-DCMV)  = 0.4950 ✗ (视觉引导读路径弱)
    - qla+qia 双通路 (M134-DUAL) = 0.4970 ✗ (不叠加, 落在两单通路之间)
    - 结论: 双通路无协同 — qia 轴未引入任何新判别信息, qla 独占 decoder-access 收益

## 5. Conclusion
  - 结论: [失败/不叠加] — DUAL (qla+qia 双通路直读 cluster KV) = 0.4970,
    -0.0040 vs qla 单通路 (M124=0.5010), 补齐矩阵后关闭 {qla,qia} 双通路假设
  - 解释: 与 M125/M126 (decoder-access × MLay 不叠加) 同形态 — 所有"增加读取通路"
    的组合均不叠加。cluster token 携带的 context 信息量有限, 无论 qla/qia/DUAL
    多少条通路去读, 拿到的都是同一份信息; qia 视觉通路贡献可忽略
  - 对后续实验设计的建议:
    ① **{qla,qia}×{cluster KV} 矩阵已全部补格** — decoder-access 轴仅 qla 有效,
       qia/DUAL 关闭, 不再扩展该轴
    ② 0.501-0.502 平台瓶颈确认在 cluster token 自身信息量 (非通路数量) —
       M136-MLAY-DCMV / M138-MLAY-DUAL / M139-MLAY-DUAL-LEGACY 预期同样不叠加,
       主要看 M140-CLICA (实例判别性监督 loss) 是否打开新信息路径
    ③ M135-DCM-S42 / M137-DCMV-S42 / M122-MLAY-S123 seed 对照继续跑,
       用于机制 vs seed-1999 归属确认, 不期待破顶
    ④ 若 M140-CLICA 也 ≈0.501 → 机制空间探尽, 需范式级新方向 (与 M139 交叉)

## 6. Crash Info
  - Error type: N/A (早停 kill, 非 crash)
  - Auto-fix attempt: N
================================================================================
