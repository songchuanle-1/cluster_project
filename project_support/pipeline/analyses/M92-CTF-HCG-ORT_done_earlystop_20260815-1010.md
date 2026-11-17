================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M92-CTF-HCG-ORT | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M92-CTF-HCG-ORT
  - Config: configs/Quard/ctf_hcg_ort/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_ort.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-14 20:11 | Finished: 2026-08-15 10:07 | Duration: ~14h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4930 | 22      |
  | Acc@50   | 0.547  | 22      |
  | spmIOU   | 0.456  | 22      |

## 3. Convergence Summary
  - Best first reached at: epoch 22 (mIoU 0.4930, Acc50 0.547, spmIOU 0.456)
  - Subsequent no_improve epochs: 11 (monitor kill PID=3221876)
  - Final epoch best: mIoU=0.4930 vs historical best=0.4930
  - 收敛形态: 稳定爬升到 ep22 见顶 (序列 0.442→0.490→0.454→0.486→0.450), 之后震荡
    11 轮未刷新, 被早停

## 4. Comparison
  - vs baseline (model_base1): γ = +0.0036 (有效, 略高于 baseline 0.4894)
  - vs current champion (A1 posA_l1): γ = -0.0082 (失败, 远低于 0.5012)
  - vs CTF×HCG 双轴 (M81 0.5012 / M90-seed123 0.4940): -0.0082 vs M81 — ORT 三轴
    组合在 CTF×HCG 基底上反降
  - vs M17-ORT (旧实现, 梯度断流伪信号 0.5005): -0.0075 — 修复梯度后 ORT 反而更差
  - vs M62-ORTG (DRP 基底, 0.4979): -0.0049 — ORT 在 CTF×HCG 基底比 DRP 基底更差

## 5. Conclusion
  - 结论: [失败] (低于 champion 0.5012, 仅略高于 baseline)
  - 解释: M92 是多样性轴的第一个"真实梯度"数据点 — ORT (尺度内正交) 在 CTF×HCG
    强基底上真实施压后 γ=-0.0082 vs champion。这证实 2026-08-14 的推断: M17-ORT
    0.5005 是梯度断流的伪信号; 修复梯度后 ORT 多样性在强基底上**有害而非增益**。
    与 M90 (CTF×HCG seed123=0.4940) 同区间, 说明 ORT 三轴组合未带来任何正交收益,
    反而破坏 CTF×HCG 的协同。
  - 对后续实验设计的建议: 多样性轴 (ORT/CSORT) 破顶希望进一步收窄。M97-CHAMP-ORT
    / M98-CHAMP-CSORT 是最后两个干净证据点 (champion 基底单变量); 若二者也持平或
    反降, 多样性轴正式闭环排除, 故事线聚焦"context 回写 + 正确交付 (CTF×HCG)",
    破顶需另寻机制 (或接受 0.5012 为 seed1999 架构上限, 转多 seed 均值论证)。

## 6. Crash Info (if crashed)
  - 无 crash。本实验为早停终止 (no_improve=11>=10)。注: 历史上 M92 曾含 3 处 bug
    (缺 orth_weight sig / 未 import / 梯度断流), 已在 2026-08-14 Phase3b 修复后
    重新入队 (bugfix_20260814-2120.md)。
================================================================================
