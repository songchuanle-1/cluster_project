================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M126-MLAY-DCM | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M126-MLAY-DCM
  - Config: configs/Quard/mlay_dcm/model_base1_quard2_c2f_enc_lite_posA_l1_mlay_dcm.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-24 17:12 | Finished: 2026-08-25 13:07 (早停 kill) | Duration: ~19.9h
  - State: done_earlystop (monitor kill PID=1435903, no_improve=11/10 ≥ patience=10)
  - Cluster attention: legacy (无 ctf/hcg/csort 解相关), cluster_att_num_layers=2 (MLay 2层),
    decoder 直读 cluster KV (DCM: decoder qla 语言通路访问)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4980 | 19/50   |
  | Acc@50   | 0.553  | 19/50   |
  | spmIOU   | 0.461  | 19/50   |
  (log best save 08:23 ep19: "mIOU: 0.498. Acc_50: 0.553. Acc_25: 0.605 / spmIOU: 0.461. spAcc_50: 0.512. spAcc_25: 0.596";
   monitor 近5次验证序列: 0.4550, 0.4900, 0.4520, 0.4900, 0.4520 — Best 后震荡回落)

## 3. Convergence Summary
  - Best first reached at: epoch 19 (mIoU=0.4980, Acc_50=0.553, spmIOU=0.461)
  - Subsequent no_improve epochs: 11/10 (monitor kill)
  - Final epoch best: mIoU=0.4980 (19/50) vs historical best=0.4980
  - 收敛形态: 快速上升后平台 (0.48-0.498), 与 MLay 系列同形态; 但平台顶 0.4980
    低于 M86-MLAY (0.5010) 与 M124-DCM (0.5010) 各 0.0030

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = +0.0086 (有效, 仍过 baseline)
  - vs MLay 单独 (M86-MLAY = 0.5010): γ = -0.0030 — 组合不及组分
  - vs DCM 单独 (M124-CTF-HCG-DCM = 0.5010): γ = -0.0030 — 组合不及组分
  - vs current champion (M95-CTF-HCG-CSORT = 0.5020): γ = -0.0040
  - 关键对照: MLay(2层) x decoder-access {DCA/DCM} 矩阵:
    - MLay x DCM (M126) = 0.4980 ✗
    - MLay x DCA (M125, running 0.4970@20/50) — 待定, 但 DCM 分支已确认无增益
    - 结论: 2层 readback + decoder KV 直读 两机制叠加无协同, 反而各退 0.003

## 5. Conclusion
  - 结论: [弱/持平] — MLay(2层) x DCM (decoder qla 直读 cluster KV) = 0.4980,
    +0.0086 vs baseline 但 -0.0030 vs 两个组分机制 (M86-MLAY / M124-DCM), 未破 0.50 平台
  - 解释: MLay (2层 legacy readback) 与 DCM (decoder qla 访问 cluster KV) 各自单独
    达 0.5010 平台, 但两者组合不能叠加, 说明两条机制共享同一信息瓶颈
    (cluster token 携带的 context 信息量有限), 叠加访问不引入新判别信息
  - 对后续实验设计的建议:
    ① M125-MLAY-DCA (MLay x DCA) 仍在跑, 若也 ≤0.50, 则 {DCA,DCM}xMLay 叠加轴
       全部关闭 — 0.5010 平台已确认饱和, 不再扩展 decoder-access x MLay 组合
    ② 0.502 平台需全新信息路径 (非 cluster 内部机制组合) 才能突破 → 关注 M120/M121
       (seed 对照 + detail 组合) 与 M134-DUAL 系列结果
    ③ M135-DCM-S42 / M137-DCMV-S42 等 seed 对照仍按队列跑, 用于机制 vs seed-1999
       归属确认, 不期待破顶

## 6. Crash Info
  - Error type: N/A (早停 kill, 非 crash)
  - Auto-fix attempt: N
================================================================================
