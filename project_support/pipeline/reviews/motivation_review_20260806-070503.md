================================================================================
  Motivation Review — cluster_project
  2026-08-06 07:05:03
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
  | 正确多尺度交付贡献 > 准单尺度 | **unverified** | 全 57+ 变体粗尺度 gather 长度错配, 0.5012 实为准单尺度 | M65-HCG 检验中 (P0) |
  | detail 残差 message 有效 | confirmed | D1=0.5003 (γ=+0.0109), 独立第二强 | 与正确交付是否协同未验 (M66) |
  | per-scale 残差 message (PSR) 有效 | unverified | M63-PSR 排队 (仍在残缺交付下) | 与正确交付是否协同**未验 (本次 M67)** |
  | orth 梯度断流假说 | unverified | M17-ORT=0.5005 但梯度断流 | M62-ORTG 重测中 |
  | 融合权重形式非瓶颈 | confirmed | SWI/CSF/SCF/QSF+detail/CSF+detail 全 < champion | 融合轴闭合 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | DRP (champion) | 0.5012 | context 回写本体 | 确认核心假设 ✓ (准单尺度) |
  | D1-detail | 0.5003 | 残差 message | 确认 message 内容轴 ✓ |
  | M17-ORT | 0.5005 | token 多样性 | 梯度断流, 待 M62 重测 |
  | M41-CTF | 0.4995 | token 质量 | 指向 readback/融合机制非 token |
  | M59-DET-QSF | 0.4961 | detail+query门控 | 排除 gate 组合 |
  | M60-DET-CSF | 0.4973 | detail+CSF 融合 | 本 tick 终态, 融合轴再闭一格 |
  | M55-SCF | 0.4927 | 内容自适应融合 | 融合权重形式收束 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (但准单尺度); detail 残差 message 有效; 融合权重/门控/
    聚合/投影放置单点均 < champion; routing 证伪。
  - 未验证: 正确多尺度交付 (HCG) 是否破 0.5012 天花板; 残差 message (detail/PSR) 在
    正确多尺度 context 下是否叠加。
  - 矛盾/疑问: 全 30+ 变体收敛 ≤0.5012 且失败集中在 message 内容/融合/投影 — 都在
    "残缺粗尺度交付" 下测得, 故事核心声称 "多尺度" 从未被正确检验。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M67-PSR-HCG 填补 {message 构造} × {交付正确性} 3×2 因子矩阵的最后一格:
      (绝对, HCG)=M65 ✓ (detail, HCG)=M66 ✓ (PSR, HCG)=**M67 本次**
    其中 PSR (M63) 在残缺交付下保留每尺度偏差, detail (D1) 把偏差融合成单标量残差;
    HCG 首次让每点收到真多尺度 context。二者组合直接回答: "当每点真多尺度时, 逐尺度
    偏差 message 是否比融合后单残差/绝对 token 更能提升定位"。
  - 若 M67 > M66/M65 → 证明 "正确交付 × 逐尺度偏差" 是故事的最优 message 形式;
    若 M67 ≈ M66 → PSR 与 detail 在正确交付下等价, 收束 message 轴;
    若 M67 < M65 → 残差 message 在正确交付下有害, 排除 PSR 方向。三态均可解释。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260806-070503.md
================================================================================
