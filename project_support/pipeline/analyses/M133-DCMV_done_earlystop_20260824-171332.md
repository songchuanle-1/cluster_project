================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M133-DCMV | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M133-DCMV
  - Config: configs/Quard/ctf_hcg_dcmv/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_dcmv.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-24 06:37 | Finished: 2026-08-24 17:07 (早停 kill) | Duration: ~10.5h
  - State: done_earlystop (monitor kill PID=46634, no_improve=11/10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4950 | 19/50   |
  | Acc@50   | 0.548  | 19/50   |
  | spmIOU   | 0.459  | 19/50   |
  (近5次验证序列: 0.4560, 0.4940, 0.4570, 0.4930, 0.4560 — Best 后震荡回落)

## 3. Convergence Summary
  - Best first reached at: epoch 19 (mIoU=0.4950, Acc_50=0.548, spmIOU=0.459)
  - Subsequent no_improve epochs: 11/10 (monitor kill)
  - Final epoch best: mIoU=0.4950 (19/50) vs historical best=0.4950
  - 收敛形态: 前期快速上升 (ep1-10: 0.47→0.49), 平台震荡 (0.487-0.495), 与 DCM M124 同形态
    但平台顶低 0.0060 (0.4950 vs 0.5010)

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = +0.0056 (有效, 刚过 baseline)
  - vs DCM qla 通路 (M124-CTF-HCG-DCM = 0.5010): γ = -0.0060 — DCMV < DCM
  - vs current champion (M95-CTF-HCG-CSORT = 0.5020): γ = -0.0070
  - 关键对照: {qla,qia}x{cluster KV} 矩阵补格结果:
    - qla 语言通路 (DCM M124) = 0.5010 ✓
    - qia 视觉/实例通路 (DCMV M133) = 0.4950 ✗
    - → decoder access 收益来自 qla 语言通路, qia 视觉通路访问 cluster KV 无增益

## 5. Conclusion
  - 结论: [失败/弱有效] — DCMV (decoder qia 视觉通路直读 cluster KV) 0.4950,
    +0.0056 vs baseline 但 -0.0060 vs DCM 同轴 qla 版本, 未达 0.50 平台
  - 解释: 与 DCM 共享 decoder KV access 假设, 但通路为 qia (视觉/实例) 而非 qla (语言)。
    结果显示访问 cluster context 的收益集中在语言通路 (query 含文本信息时最有效),
    视觉通路 query 访问多尺度 cluster token 不引入判别性信息, 机制贡献为负或中性
  - 对后续实验设计的建议:
    ① M137-DCMV-S42 (seed=42 对照) 按原计划跑, 验证 qia 通路 0.4950 是否为
       seed-1999 红利 — 但大概率确认 qia 轴弱, 该方向不再扩展
    ② qla 通路 DCM 已收敛于 0.5010 平台, decoder-access 轴已完成 {qla,qia}x{KV}
       矩阵, 可转向 M125/M126 (MLay 2层 x DCA/DCM) 叠加验证是否破顶
    ③ 若 2层注入 + decoder access 叠加仍 ≤0.502, 平台已饱和, 需全新信息路径

## 6. Crash Info
  - Error type: N/A (早停 kill, 非 crash)
  - Auto-fix attempt: N
================================================================================
