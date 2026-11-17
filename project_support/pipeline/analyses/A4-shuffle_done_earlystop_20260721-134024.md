================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: A4-shuffle | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: A4-shuffle
  - Config: configs/Quard/trueroute_shuffle/model_base1_quard2_c2f_enc_lite_posA_l1_trueroute_shuffle.yaml
  - Server: server-4 | GPU: 1
  - State: done_earlystop

## 2. Best Metrics
  | Metric | Value | @ Epoch |
  |--------|-------|---------|
  | mIoU   | 0.4941 | ~19     |
  | Acc@50 | 0.510  | —       |
  | spmIOU | 0.457  | —       |

## 3. Convergence Summary
  - Best first reached at: epoch ~19 (0.4941)
  - 收敛形态: 上升后震荡, 最终 0.4867

## 4. Comparison
  - vs A3 (TrueRoute=0.4468): γ = +0.0473 (大幅优于正确路由!)
  - vs champion (Lite=0.5012): γ = −0.0071 (仍低于无路由)
  - vs A1 (champion=0.5012): γ = −0.0071

## 5. Conclusion
  - 结论: [关键控制组] — 内容路由 HARMFUL (正确路由比随机差)
  - 解释: A4(随机路由 0.4941) >> A3(正确路由 0.4468), 证明 top-k 内容路由
    有害; A4 < A1(无路由 0.5012), 路由结构本身有轻微副作用.
    论文故事: cluster_attn 收益来自多尺度 context, 内容路由被 A4 控制组证伪.
  - 建议: routing 路线放弃, 专注多尺度 context 机制
