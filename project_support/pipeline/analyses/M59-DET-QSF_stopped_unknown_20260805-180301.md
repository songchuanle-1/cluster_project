================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M59-DET-QSF | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M59-DET-QSF
  - Config: configs/Quard/det_qsf/model_base1_quard2_c2f_enc_lite_posA_l1_det_qsf.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-04 22:03:47 | Finished: 2026-08-05 ~14:30 (ep29 早停, 进程随后消失) | Duration: ~16.5h
  - State: stopped_unknown (monitor 按死亡进程 deathwatch ×3 判定; 远端日志确认实际为训练脚本
    ep29 早停退出 — 语义等价 done_earlystop, 非 crash)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4961 | 29/50   |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (远端日志: "Early stopping at epoch 29: no improvement for 10 epochs (best=0.4961)" —
   训练脚本自身早停, best 已保存 checkpoint)

## 3. Convergence Summary
  - Best first reached at: epoch 29 (监控曲线 3/50=0.3719 → 6/50=0.4565 → 22/50=0.4961 → 29/50 平台)
  - Subsequent no_improve epochs: 10/10 (训练脚本在 ep29 触发 patience 早停)
  - 收敛形态: 前 6 ep 快速爬升, 之后 20+ ep 缓慢爬升逼近 0.496 后平台, 未能挑战 champion 0.5012

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0067 (有效, 高于 baseline)
  - vs current champion (DRP/posA_l1 0.5012): γ = -0.0051 (失败)
  - vs detail 单独 (D1-detail 0.5003): γ = -0.0042 (detail+QSF 组合 < detail 单独)
  - vs QSF 单独 (M6-QSF 0.4866): γ = +0.0095 (叠加 detail 有提升, 但整条 gate 系仍 < champion)
  - 组合轴对照: DET-ORT(无指标, 1/50 静默死亡, GPU7 过载) / DET-DRP(running) /
    DET-CSF(running 0.4775@9ep) / DET-QSF(0.4961@29ep)

## 5. Conclusion
  - 结论: [失败]
  - 解释: detail message 之上叠加 query 尺度门控 (QSF) 无增益 — 0.4961 < detail 单独 0.5003,
    且 QSF 自身属已 banned 的 gate 系 (M6-QSF=0.4866, M1-QGC=0.4939 均已败)。query 驱动的
    尺度选择与 detail 精细 message 无协同, 进一步收束 "门控/融合权重形式非瓶颈" 的结论。
  - 对后续实验设计的建议: 不再设计 QSF/query 门控相关组合 (gate 系闭环)。组合轴剩余待验证:
    M58-DET-DRP (detail+去路由) 与 M60-DET-CSF 仍 running; readback 尺度交付补格 (M65-HCG/
    M66-DET-HCG) 与 message 构造 (M63-PSR/M64-SSP) 继续排队。

## 6. Crash Info (if crashed)
  - 无 crash — 训练脚本正常 early-stop 退出 (ep29 best=0.4961); monitor 因进程消失未读到
    终态标志, deathwatch ×3 后归档为 stopped_unknown。已从 deathwatch/running.json 移除,
    gpu1 槽已由 M61-SCT 复用。
================================================================================
