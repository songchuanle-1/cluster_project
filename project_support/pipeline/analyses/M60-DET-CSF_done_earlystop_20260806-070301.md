================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M60-DET-CSF | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M60-DET-CSF
  - Config: configs/Quard/det_csf/model_base1_quard2_c2f_enc_lite_posA_l1_det_csf.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-05 11:26:07 | Finished: 2026-08-06 ~06:10 | Duration: ~18.7h
  - State: done_earlystop (远端日志 "Early stopping at epoch 25: no improvement for 10 epochs
    (best=0.4973)", 训练脚本自身早停退出, 进程消失被 monitor deathwatch 捕捉)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4973 | 25/50   |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch 25 (监控曲线 8/50=0.4775 → 23/50=0.4973 → 25/50 平台, 早停)
  - Subsequent no_improve epochs: 10/10 (ep25 触发 patience=10 早停)
  - 收敛形态: 前 8 ep 快速爬升后缓慢逼近 0.497, 25 ep 平台后早停, 未能挑战 champion 0.5012

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0079 (有效)
  - vs current champion (DRP/posA_l1 0.5012): γ = -0.0039 (失败)
  - vs detail 单独 (D1-detail 0.5003): γ = -0.0030 (detail+CSF 组合 < detail 单独)
  - vs CSF 单独 (M44-CSF 0.4958): γ = +0.0015 (叠加 detail 有轻微提升, 但整条 CSF+ 组合线仍 < champion)
  - 组合轴对照: DET-QSF(0.4961)/DET-CSF(0.4973) 全 < detail 单独; DET-DRP(M58, running) /
    DET-ORT(1/50 过载死亡) 待验

## 5. Conclusion
  - 结论: [失败]
  - 解释: detail message 之上叠加 content-scale 融合 (CSF) 无增益 — 0.4973 < detail 单独
    0.5003, 与 M59-DET-QSF 结论一致: detail 的残差 message 收益在叠加融合权重形式
    (QSF/CSF) 时被稀释, 融合权重形式非瓶颈, 与 SCF/SWI/CSF 单点结论 (融合轴收束) 互相印证。
  - 对后续实验设计的建议: 不再设计 detail+融合权重 组合 (QSF/CSF 双败, 融合轴闭环)。
    组合轴剩余有效对照: M58-DET-DRP (detail+DRP 本体) 仍 waiting, 是 detail 与
    champion 机制直接组合的唯一待验格; readback 交付补格 (M65-HCG/M66-DET-HCG) 与
    message 构造 (M63-PSR) / 投影放置 (M64-SSP) 继续排队。

## 6. Crash Info (if crashed)
  - 无 crash — 训练脚本正常 early-stop (ep25 best=0.4973); monitor 因进程消失 deathwatch
    判定前已确认日志早停, 语义等价 done_earlystop。gpu0 槽已由 M62-ORTG 复用 (07:03 推送)。
================================================================================
