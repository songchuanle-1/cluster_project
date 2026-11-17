================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M82-DET-CTF | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M82-DET-CTF
  - Config: configs/Quard/det_ctf/model_base1_quard2_c2f_enc_lite_posA_l1_det_ctf.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-11 21:16:02 | Finished: 2026-08-12 10:13:51 | Duration: ~13h
  - State: stopped_unknown (process interrupted, 22/50 epochs completed)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4989 | ≤22     |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (日志未拉取成功，Acc@50/spmIOU 缺失；checkpoint 留远端)

## 3. Convergence Summary
  - Best first reached at: epoch ≤22 (递增中被打断，未收敛到平台)
  - 22/50 epochs completed; 早停 patience 未触发，属中途打断
  - 收敛形态: 前 22 epoch 上升中即被终止（server-4 槽位被 M83 resume 占用，见 M81 同批中断）

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0095 (有效)
  - vs champion (model_...posA_l1 0.5012): γ = -0.0023 (未达 champion，但仅 22/50 未收敛)
  - vs M41-CTF 单轴 (0.4995): γ = -0.0006 (detail 叠加在 CTF 上当前未见增益)
  - vs M81-CTF-HCG (0.5012): γ = -0.0023 (detail 组合弱于 HCG 组合)

## 5. Conclusion
  - 结论: [持平偏弱]（未收敛，结论不充分）
  - 解释: CTF(detail) = 0.4989@22ep，detail message_type 与 CTF token 精炼轴的叠加在中断时
    未显示增益（与 M81 CTF×HCG 的 +0.0118 synergy 形成对比）。detail 可能偏"交付方式"，
    与 HCG（正确多尺度交付）功能重叠，增益有限。
  - 对后续实验设计的建议:
    (a) 不单独追 M82 路线；detail 与 CTF 叠加收益弱于 detail×HCG×CTF 三维组合（M84 已入队）
    (b) M84-DET-CTF-HCG (CTF×HCG×detail) 正在 server-4 gpu0 运行，将直接检验三维组合
    (c) 若 M84 增益显著 → detail 贡献依赖 HCG 协同；若 M84 ≈ M81 → detail 轴可搁置
================================================================================
