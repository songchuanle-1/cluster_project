================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M142-CTF-HCG-CLICA-CSIC | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M142-CTF-HCG-CLICA-CSIC
  - Config: configs/Quard/ctf_hcg_clica_csic/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_clica_csic.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-28 (M142 推送后) | Finished: 2026-08-28 11:07:25 | Duration: ~1d
  - State: done_earlystop (monitor kill, PID=485998)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4890 | 19      |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch 19 (no_improve 11/10 触发早停)
  - Subsequent no_improve epochs: 11 (monitor kill)
  - Final epoch best: 0.4890
  - 收敛形态: 峰值出现在 ep19 后即进入平台/衰减，最终被早停 kill

## 4. Comparison
  - vs ctf_hcg base (M81=0.5012): γ = -0.0122 (失败)
  - vs baseline model_base1 (0.4894): γ = -0.0004 (持平)
  - vs CLICA 单独 (M140=0.4970): γ = -0.0080
  - vs CSIC 单独 (M141=0.4960): γ = -0.0070
  - 结论: CLICA×CSIC 双监督组合比任一单独更差，loss 轴组合无协同反有害

## 5. Conclusion
  - 结论: [失败]
  - 解释: 判别性对齐 (cluster_inst_align) 与跨尺度一致 (cluster_consistency) 两个
    aux loss 叠加在 ctf_hcg base 上，比单独任一都低 0.007-0.008，比 base 低 0.0122。
    与 M140/M141 一起构成 loss 监督轴第 3 连败，且是"双 loss 组合"格的闭合证据:
    loss 轴内组合不叠加，甚至相互干扰。
  - 对后续实验设计的建议: loss 轴组合方向关闭。等待 M143-OBJG / M144-LQA 两个
    正交监督维终态后再判定 loss 轴整体生死; 若 OBJG/LQA 也 < base 0.5012，
    loss 监督轴 5 连败 → 关闭该轴。

## 6. Crash Info (if crashed)
  - N/A (早停 kill, 非 crash)
================================================================================
