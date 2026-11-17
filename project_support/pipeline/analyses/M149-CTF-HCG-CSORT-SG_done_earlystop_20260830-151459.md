================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M149-CTF-HCG-CSORT-SG | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M149-CTF-HCG-CSORT-SG
  - Config: configs/Quard/ctf_hcg_csort_sg/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_sg.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-30 03:09 | Finished: 2026-08-30 15:07 | Duration: ~12h
  - State: done_earlystop (no_improve=11/10, monitor kill PID=3494698)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4940 | 20/50   |
  | Acc@50   | 0.547  | 20      |
  | spmIOU   | 0.458  | 20      |
  (best.pth 保存于 Val[17/50]; monitor 序列计数 20. 近5次验证: 0.456/0.493/0.457/0.492/0.454)

## 3. Convergence Summary
  - Best first reached at: ~epoch 17-20 (log save Val[17], monitor 20/50)
  - Subsequent no_improve epochs: 11 (early-stopped by monitor, patience=10)
  - Final epoch best: mIoU=0.4940 vs historical best=0.4940
  - 收敛形态: 快速上升至 ~0.493 平台后小幅冲顶 0.494, 之后 0.456-0.492 震荡无刷新

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0046 (勉强有效, 幅度显著小于 CSORT)
  - vs champion (M95-CTF-HCG-CSORT 0.5020): γ = -0.0080 (未破顶)
  - vs CSORT 对称版 (M95=0.5020): SG 非对称版掉 0.0080 → **对称 abs-cosine 追逐
    项是收益的负载部件**, 移除对称性(单侧 stop-gradient)不改善反而丢分
  - vs 同 batch M145-ALL(0.4920)/M146-DET(0.4970): SG 0.4940 处于中间水平, 无上分

## 5. Conclusion
  - 结论: [失败] (对 champion 而言)
  - 解释: SG 假设 — "对称双侧更新形成追逐反馈环, 造成 CSORT 跨 seed 脆弱" —
    被证伪: 单侧 stop-gradient 非对称去相关 (BYOL/SimSiam 风格) 从 0.5020 掉到
    0.4940, 说明对称 abs-cosine 双向往推不是脆弱来源, 反而贡献了 seed-1999 的
    去相关收益。CSORT 跨 seed 脆弱 (s42=0.494/s123=0.493/s2026=0.490) 另有原因,
    非追逐环结构问题。
  - 对后续实验设计的建议: 关闭"非对称去相关"方向。CSORT 对称项保留。seed 脆弱
    的修复不再走 loss 结构路线; 剩余在队实验 (M150-OWC/M151-ODW 写回正交,
    M152/M156 尺度范围, M154-GSC 全局尺度, M155-RF 精炼 token 对齐) 继续从
    "操作对象/信息路径"角度找破 0.5020 的机会。

## 6. Crash Info (if crashed)
  - 无 crash。正常 early-stop。
================================================================================
