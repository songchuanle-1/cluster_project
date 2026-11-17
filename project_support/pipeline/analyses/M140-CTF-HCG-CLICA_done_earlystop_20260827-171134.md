================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M140-CTF-HCG-CLICA | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M140-CTF-HCG-CLICA
  - Config: configs/Quard/ctf_hcg_clica/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_clica.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-27 04:25:55 (relaunch 042555; 首发 040923 因 IndexError crash)
  - Finished: 2026-08-27 17:07:26 (monitor 早停 kill, PID 1906005)
  - Duration: ~12.7h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4970 | ~17     |
  | Acc@50   | 0.548  | 19      |
  | spmIOU   | 0.457  | 19      |
  (best val 序列: 0.224→0.435(ep4)→0.4907(ep11)→0.4970(ep17)→0.4848→0.4943(ep21)→0.4867(ep24))

## 3. Convergence Summary
  - Best first reached at: epoch ~17 (last save best.pth 13:32:03)
  - Subsequent no_improve epochs: 13/10 (patience=10) → monitor kill
  - Final epoch best: 0.4867 vs historical best 0.4970
  - 收敛形态: 前 17 epoch 稳步上升 (0.224→0.4970), 之后平台震荡回落, 无二次上升

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0076 (有效)
  - vs current champion (M95-CTF-HCG-CSORT 0.5020): γ = -0.0050 (未破顶)
  - vs M134-DUAL (qla+qia 双通路, 0.4970): 持平 — CLICA 与 DUAL 落在同一水平
  - vs M124-CTF-HCG-DCM (0.5010) / M119-CTF-HCG-MFP (0.5020): 低 0.0040-0.0050

## 5. Conclusion
  - 结论: [有效但未破顶]
  - 解释: 同尺度实例判别 loss (cluster-instance contrastive align) 单轴监督 cluster token,
    0.4970 高于 baseline +0.0076, 但未突破 champion 0.5020 — 判别性 loss 单维度不足以突破
    token 信息瓶颈, 与 DUAL 双通路 (M134=0.4970) 同水平, 说明该轴已饱和.
  - 对后续实验设计的建议: M141-CSIC (跨尺度一致) / M143-OBJG (目标感知) / M144-LQA (语言语义)
    继续检验其它正交监督维度; M142 (CLICA×CSIC 双 loss) 验证判别×一致组合是否 > 单轴.
    若 4 loss 维全部 < 0.5020, 则 token 监督轴整体弱于结构/交付轴 (MLay/HCG/CSORT), 方向回调.

## 6. Crash Info (if crashed)
  - Error type: IndexError (cluster_ids 层级组合映射)
  - Error message excerpt: "IndexError: mask[1586] vs tensor[256]"
  - Auto-fix attempt: Y — 1 retry, 修复 lvl>0 簇 id 未组合回超点映射 (commit 788f171), result: fixed
================================================================================
