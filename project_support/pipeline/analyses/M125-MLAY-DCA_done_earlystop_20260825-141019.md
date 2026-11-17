================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M125-MLAY-DCA | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M125-MLAY-DCA
  - Config: configs/Quard/mlay_dca/model_base1_quard2_c2f_enc_lite_posA_l1_mlay_dca.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-24 16:13 | Finished: 2026-08-25 14:07 (早停 kill) | Duration: ~21.9h
  - State: done_earlystop (monitor kill PID=1312169, no_improve=11/10 ≥ patience=10)
  - Cluster attention: legacy (无 ctf/hcg/csort 解相关), cluster_att_num_layers=2 (MLay 2层),
    decoder 直读 cluster KV (DCA: decoder qia 视觉通路访问)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4970 | 20/50   |
  | Acc@50   | 0.552  | 20/50   |
  | spmIOU   | 0.460  | 20/50   |
  (log best save: "mIOU: 0.497. Acc_50: 0.552. Acc_25: 0.602 / spmIOU: 0.460. spAcc_50: 0.512";
   monitor 近5次验证序列: 0.4560, 0.4970, 0.4600, 0.4950, 0.4570 — Best 后震荡回落)

## 3. Convergence Summary
  - Best first reached at: epoch 20 (mIoU=0.4970, Acc_50=0.552, spmIOU=0.460)
  - Subsequent no_improve epochs: 11/10 (monitor kill)
  - Final epoch best: mIoU=0.4970 (20/50) vs historical best=0.4970
  - 收敛形态: 快速上升后平台 (0.49-0.497), 与 MLay 系列同形态; 平台顶 0.4970
    低于 M86-MLAY (0.5010) 与 M126-MLAY-DCM (0.4980)

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = +0.0076 (有效, 仍过 baseline)
  - vs DCA 单独 (M51-DCA = 0.4893): γ = +0.0077 — MLay 2层叠加 DCA 高于 DCA alone,
    但远低于 MLay 单独平台
  - vs MLay 单独 (M86-MLAY = 0.5010): γ = -0.0040 — 组合不及组分
  - vs sister cell MLay x DCM (M126 = 0.4980): γ = -0.0010 — DCA/DCM 两分支同形态
  - vs current champion (M95-CTF-HCG-CSORT = 0.5020): γ = -0.0050
  - 关键对照: MLay(2层) x decoder-access {DCA/DCM} 矩阵:
    - MLay x DCM (M126) = 0.4980 ✗
    - MLay x DCA (M125) = 0.4970 ✗
    - 结论: {qia(DCA), qla(DCM)} x MLay 叠加轴**全部关闭** — 两条 decoder-access
      通路与 2层 readback 组合均无协同, 不引入新判别信息

## 5. Conclusion
  - 结论: [弱/持平] — MLay(2层) x DCA (decoder qia 直读 cluster KV) = 0.4970,
    +0.0076 vs baseline 但 -0.0040 vs MLay 组分 (M86=0.5010), 未破 0.50 平台
  - 解释: 与 M126 (MLay x DCM = 0.4980) 完全同形态 — 2层 readback + decoder KV
    直读两机制叠加无协同, 各退 ~0.003-0.004。印证 M126 结论: 两条机制共享同一
    信息瓶颈 (cluster token 携带的 context 信息量有限), decoder qia/qla 访问
    都不引入新判别信息
  - 对后续实验设计的建议:
    ① **{DCA,DCM} x MLay 叠加轴已确认全部关闭** — 不再扩展 decoder-access x MLay 组合
    ② 0.501-0.502 平台由 seed-1999 结构性红利决定 (CTF-HCG mean ~0.498),
       需全新信息路径才能突破 → 关注 M134-DUAL (qla+qia 双通路在 ctf_hcg base)
       与 M138/M139 (满强度正交组合) 结果
    ③ M135-DCM-S42 / M137-DCMV-S42 / M122-MLAY-S123 seed 对照按队列跑,
       用于机制 vs seed-1999 归属确认, 不期待破顶
    ④ M139-MLAY-DUAL-LEGACY (legacy 2层 x qla+qia 双通路) 是当前唯一未测
       且 base 正确的组合格; 若其 ≈0.501 则当前机制空间探尽, 需范式级新方向

## 6. Crash Info
  - Error type: N/A (早停 kill, 非 crash)
  - Auto-fix attempt: N
================================================================================
