================================================================================
  Motivation Review — cluster_project
  2026-08-24 03:13:17
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999,
    CSORT 轴已关闭, 0.5020 归因 seed-1999 红利)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-24 03:07:35: Phase 1 NOT YET, continue exploring
  - 活跃保留: goal.json constraints 无"活跃保留"条款 (07-19 已解除);
    最近 24h 无未决 question (仅 server-6 慢速/配置类, 已resolve) → 可自主设计

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 ≥ 0.005 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012, γ=-0.0544 | 关闭 |
  | decoder 直接访问 cluster tokens (方向①) | partial | DCM=0.5010 (qla 共享通路) > DCA=0.4970 (专用分支); 平台未破 | **qia 视觉通路未测** |
  | 多层注入 (方向②) | partial | MLay 2层=0.5010; 3/4/6层重复注入已证退化 (banned) | 与其它机制叠加未定 |
  | MFP (masked feature prediction) | unconfirmed | M119=0.5020 tie champion (seed1999) — 唯一不伤的 encoder-side 机制 | seed 矩阵判定中 (M129/M130 running) |
  | encoder-side token 质量轴 (CCL/CGA/BCF/SRL/MEMBANK) | 证伪 | 0.489-0.493 全灭 | 关闭 |
  | CSORT 跨 scale 去相关 | 证伪 | 3/4 seed 负, 0.5020 归因 seed1999 | 关闭 |
  | decoder-access 2×2 {context/detail}×{DCA/DCM} | 完成 | DCM 最优 0.5010, 其余 ≤0.499 | 矩阵已满格, 无格破顶 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|--------------|
  | M119-MFP | 0.5020 | 特征级 mask 重建 aux loss 提升 cluster token 完整性 | encoder-side 唯一不伤, tie champion (seed1999, 机制性未定) |
  | M124-DCM | 0.5010 | decoder query 经 qla 语言通路共享 KV 读 cluster context | decoder-access 轴最优 (0.5010); **验证共享通路优于专用分支 (DCA 0.4970)** |
  | M123-DCA | 0.4970 | decoder query 专用分支 cross-attend cluster | 弱于 DCM, 轴内对比淘汰 |
  | M86-MLAY | 0.5010 | 2层注入 (方向②) | 多层注入有效但平台饱和 |
  | M128-DET-DCM | 0.4990 | detail message × DCM | detail 对 DCM 无正叠加, 2×2 满格 |
  | M127-DET-DCA | 0.4870 | detail message × DCA | detail×DCA 负交互, 轴内证伪 |
  | M129-MFP-S42 / M130-MFP-S123 | running | MFP seed 对照 | 判定 MFP 机制性 (关键) |
  | M81-CTF-HCG | 0.5012 | 正确多尺度交付 | 稳定 ~0.501 平台 (跨 seed mean ~0.498) |
  | M95-CTF-HCG-CSORT | 0.5020 | 跨 scale 正交化 | seed1999 outlier, 轴已关闭 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); decoder-access 轴 DCM 最优 (0.5010,
    qla 共享通路 > DCA 专用分支); 2层注入有效 (0.5010); MFP 不伤 (0.5020, 未定机制性)。
  - 未验证: ① MFP 是否真实机制 (M129/M130 running); ② decoder-access 与其它
    独立机制叠加能否破 ~0.501 平台 (M125/M126/M131 排队); ③ **decoder 视觉通路
    (qia) 直接读 cluster context 是否有效 — 从未测试**。
  - 关键洞察: DCM 证明了"decoder 侧直接访问 cluster tokens 绕过 writeback 有损瓶颈"
    在**语言通路 (qla)** 有效 (0.5010)。但 decoder 的**视觉/实例通路 (qia)**
    从未注入 cluster context — 该假设是对称的: 若 DCM 的机制是通路不变
    (pathway-invariant), qia 通路同样应能从多尺度 cluster context 受益;
    这是 decoder-access 轴 {qla, qia} × {cluster KV 扩展} 2×2 矩阵的缺格。
  - 组合历史警示: CCP×HCG=0.4950, CCP×detail=0.4952, REAGG×HCG=0.5008,
    detail×DCM=0.4990 (无协同) — 组合并非必然加性; 但 qia 通路是**单一机制**扩展,
    非组合, 直接检验 DCM 机制的通用性。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体: M133-DCMV (DCM-Visual) — decoder query 经 qia 视觉/实例通路共享 KV
    读多尺度 cluster tokens。
  - 因果假设: DCM 已验证"decoder 直接读 cluster context 绕过 writeback 单通道
    有损瓶颈"在语言通路有效 (0.5010)。若该机制通路不变, qia 通路 (decoder query
    先于 qla 直接 attend inst_feats + cluster tokens) 应产生等价或正交的上下文
    增益。这直接补上 motivation_review 反复标注的 "qia 视觉通路未测" 缺格。
  - 机制贡献: 若 DCMV > 0.501 → 证明 decoder-access 收益是通路不变的,
    decoder 双侧 (语言+视觉) 都可作为 cluster context 出口, 故事线从"qla 单通路"
    推进到"双通路 decoder 访问"; 若 ≈0.501 → 确认 qla 已捕获 decoder 侧
    cluster 访问的全部可及收益, 视觉通路无额外信息。
  - 与 banned[]/constraints 校验: 非 gate/非 langroute/非 attnpool/非 residual/
    非 true_route/非 3-6 层注入; 无新增参数 (仅 KV concat, 复用 qia 已有注意力);
    不改变数值分布/温度/缩放; 无新超参。不违反任何条款。
  - 条件独立性: 本变体**不依赖 MFP seed 结果** — 即使 M129/M130 证伪 MFP 导致
    M131/M132 撤回, M133 仍有效, 保持队列深度。
  - 排除方向: 不设计纯 seed 变体 (M129/M130/M122 已覆盖)、不设计 3/4/6 层注入
    (banned)、不设计 gate 系 (banned)、不设计 N² attention (用户保留)、
    不设计 encoder-side 新 token 质量机制 (轴证伪)、不设计 DCM×DCA 组合
    (两条通路同层叠加风险未明, 且 qia 单点未测)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260824-031317.md
================================================================================
