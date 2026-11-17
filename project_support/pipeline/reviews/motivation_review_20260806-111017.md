================================================================================
  Motivation Review — cluster_project
  2026-08-06 11:08:00
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云
    特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'
    假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: DRP/posA_l1 0.5012 (done_complete 36/50)
  - Gap: +0.0088 | Phase 1 (NOT YET) — 继续自主设计服务指标提升
  - 硬约束: FLOPs≤10G / 禁改 schedule / Phase1 禁调参只许结构性机制变更 / 分支停止<0.002 /
    cluster 只更新 inst_feats / 默认仅最后1层注入 / 禁 N² attention / seed 1999
  - banned: gate系/语言路由系/attnpool/qcond/agg/multi/prune/nomask扩展/3-4-6层重复注入/
    大型QKVO/true_route/residual系(B5/E4)/Phase1 调参系

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1−A0=+0.0118 (champion 0.5012 vs base 0.4894) | 需消融哪些设计必要 |
  | 显式 routing 有独立收益 | refuted | A3−A1=-0.0544 (TrueRoute 0.4468) | — |
  | 正确多尺度交付贡献 > 准单尺度 | **unverified** | 全 57+ 变体粗尺度 gather 长度错配 | M65-HCG 检验中 (P0) |
  | detail 残差 message 有效 | confirmed | D1=0.5003 (γ=+0.0109) | 与正确交付协同 M66 排队 |
  | per-scale 残差 message (PSR) 有效 | unverified | M63-PSR 排队 (残缺交付) | HCG 协同 M67 排队 |
  | per-scale 独立投影 (SSP) 有效 | unverified | M64-SSP 排队 (残缺交付) | HCG 协同 **本次 M68** |
  | 顺序依赖 readback (粗→细) | refuted | M61-SCT=0.4854 < baseline (本 tick 终态) | 顺序依赖子维度闭合 |
  | orth 梯度断流假说 | unverified | M17-ORT=0.5005 梯度断流 | M62-ORTG 重测中 |
  | 融合权重形式非瓶颈 | confirmed | SWI/CSF/SCF/QSF+detail/CSF+detail 全 < champion | 融合轴闭合 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | DRP (champion) | 0.5012 | context 回写本体 | 确认核心假设 ✓ (准单尺度) |
  | D1-detail | 0.5003 | 残差 message | 确认 message 内容轴 ✓ |
  | M17-ORT | 0.5005 | token 多样性 | 梯度断流, 待 M62 重测 |
  | M41-CTF | 0.4995 | token 质量 | 指向 readback/融合机制非 token |
  | M55-SCF | 0.4927 | 内容自适应融合 | 融合轴收束 |
  | M59-DET-QSF | 0.4961 | detail+query门控 | gate 组合排除 |
  | M60-DET-CSF | 0.4973 | detail+CSF | 融合轴再闭一格 |
  | M61-SCT | **0.4854** | 顺序 readback (粗→细) | **本 tick 终态: 顺序依赖子维度闭合** |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (但准单尺度); detail message 有效; 融合权重/门控/聚合/顺序
    依赖全 < champion; routing 证伪。
  - 未验证: 正确多尺度交付 (HCG) 是否破 0.5012 天花板; 残差 message (detail/PSR) 在正确
    交付下是否叠加; **per-scale 独立投影在正确交付下是否叠加**。
  - 矛盾/疑问: M64-SSP 的 per-scale 投影在残缺交付下测得 — 粗尺度(8/64 簇)对多数点是 0,
    per-scale 投影在粗尺度上被零信号浪费, SSP 的因果机制无法充分显现。只有 HCG 正确
    交付让每点收到真粗尺度信号后, per-scale 投影才有机会工作。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M68-SSP-HCG 填补 {投影放置}×{交付正确性} 2×2 因子矩阵的最后一格:
      (共享投影, broken)=champion 0.5012 ✓
      (per-scale 投影, broken)=M64-SSP (排队)
      (共享投影, HCG)=M65-HCG (排队)
      (per-scale 投影, HCG)=**M68-SSP-HCG 本次**
    其中 SSP (M64) 的因果机制是"每尺度在自身粒度下独立变换后再融合", 但该机制
    依赖每尺度信号真实送达 — 残缺交付下粗尺度为 0, 机制被抑制; HCG 首次让每点
    收到真多尺度 context。二者组合直接回答: "当粗尺度信号真送达时, per-scale
    独立投影是否比共享投影更优"。
  - 若 M68 > M65/M64 → 证明 "正确交付 × per-scale 投影" 是更优 readback 结构;
    若 M68 ≈ M65 → SSP 与共享投影在正确交付下等价, 收束投影轴;
    若 M68 < M65 → per-scale 投影在正确交付下有害, 排除 SSP 方向。三态均可解释。
  - 与已接受先例同构: M66-DET-HCG (detail+HCG)、M67-PSR-HCG (PSR+HCG) 均为
    "已入队单点机制 × 正确交付" 因子补格, M68 是投影放置轴的同构补格。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_<ts>.md
================================================================================
