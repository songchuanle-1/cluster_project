================================================================================
  Motivation Review — cluster_project
  2026-08-04 22:09:14
================================================================================

## 1. Goal
  - goal.json description: cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云
    特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类
    路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51。
  - Target: mIoU ≥ 0.5100 | Champion: posA_l1 (DRP) 0.5012 | Gap: +0.0088 | Phase 1 (NOT YET)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | DRP 0.5012 vs base 0.4894 (γ=+0.0118) | 需消融哪些设计必要 (Phase 2) |
  | routing 生效反降点 | confirmed(证伪) | TrueRoute 0.4468 vs DRP 0.5012 | — |
  | readback expressiveness 非瓶颈 | confirmed | BIL/NLR/FILM/FLM/DGC 全 < champion | 轴闭合 |
  | 聚合 = mean 最优 | partial | max/weighted/dual 全 < mean; CCR/VAC/SAC 在跑 | 等待聚合轴收束 |
  | token 质量非瓶颈 | confirmed | CTF 0.4995 (token FFN) | — |
  | token 多样性(正交)有帮助 | 未验证(bug 污染) | M17-ORT 梯度断流; M62-ORTG 已入队 | 重测中 |
  | message 构造轴 | closing | 绝对-逐尺度(DRP 0.5012) / 残差-融合后(D1 0.5003) / 残差-逐尺度(PSR 已入队) | 待 PSR 收束 |
  | 融合机制轴 | testing | SCF(内容注意力, running) / SCT(顺序, waiting) | 待收束 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | DRP (champion) | 0.5012 | 直接验证 context 回写 (绝对 token, 逐尺度 gate 融合, 共享 post-fusion 投影) | 确认核心假设 ✓ |
  | D1-detail | 0.5003 | 融合后单残差 message | 残差方向有效但 < 绝对 |
  | M17-ORT | 0.5005 | token 正交正则 | 无效(bug 污染), 重测中 |
  | M50-DGC | 0.4913 | diff-gated readback | 失败 → readback expressiveness 轴闭合 |
  | M51-DCA | 0.4893 (本 tick 终态) | dual pooling (mean+max) 聚合 | 失败 → mean 聚合仍最优 |
  | M45-NCR | 0.4980 | soft readback | 有效但 < hard-gather DRP |
  | M41-CTF | 0.4995 | token FFN | 有效但非瓶颈 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效、routing 有害、readback expressiveness 非瓶颈、token 质量
    非瓶颈、mean 聚合 ≥ 双分支聚合。
  - 未验证/在队列: 聚合质量 (CCR/VAC/SAC running)、token 多样性 (M62-ORTG)、顺序依赖
    (M61-SCT)、内容融合 (M55-SCF)、message 构造 (M63-PSR)、detail 组合 (M58/59/60)。
  - **从未触过的结构轴: readback message 的"投影放置"**。所有 30+ 变体 (含 champion) 均
    用单一共享投影 point_out_proj 在融合后投影 fused message。**从未在融合前给每个尺度
    独立投影**。细尺度(256) token 描述实例级细节, 粗尺度(8) token 描述场景级布局 —
    二者与 inst_feats 的语义空间不同, 共享投影是折中。此轴与 message 构造轴 (绝对/残差)
    和融合轴 (SCF/SCT) 正交。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M64-SSP (Scale-Specialized Projection): 每尺度 cluster token 先经独立 Linear 投影
    (scale_projs), 再逐尺度 gate 融合; 替换 champion 的共享 post-fusion point_out_proj。
    - 填补缺口: "投影放置"轴 — champion 融合后单投影 vs SSP 融合前逐尺度投影。
    - 变体角色: 验证假设 "各尺度 context 需在自身语义粒度下变换后再融合; 单一共享
      投影强制所有尺度经同一线性变换, 丢失尺度特异语义".
    - 对照基线: DRP champion 0.5012。SSP > 0.5012 → 投影放置是瓶颈; ≈0.5012 →
      该轴闭合, readback 机制三轴 (expressiveness/message/投影) 证据链完整。
    - 与在队列变体正交: PSR 改 message 源(残差), SCF/SCT 改融合权重, SSP 改 message 变换。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260804-220914.md (M64-SSP 单变体)
================================================================================
