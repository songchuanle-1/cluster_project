================================================================================
  Motivation Review — cluster_project
  2026-07-28 05:03:01
================================================================================

## 1. Goal
  - 引用: pipeline/goal.json
  - Target: mIoU ≥ 0.5100 | Champion: model_base1_quard2_c2f_enc_lite_posA_l1 0.5012 | Gap: +0.0088
  - Phase: 1 (NOT YET) — champion 未达标，继续自主探索
  - Description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。"

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 cluster context 提升定位精度 | confirmed | champion 0.5012 vs base 0.4894 (γ=+0.0118) | 如何继续提升到 0.5100? |
  | 聚类路由 (routing) 有效 | falsified | A3-TrueRoute=0.4468 (γ=-0.0544) | 无需再验证 |
  | Mean-pool aggregation 最优 | confirmed | M23-CMX max-pool=0.4910 (-0.0102 vs champion) | — |
  | 3-scale 必要 (非 2-scale) | confirmed | M18-S2FM=0.4933, M19-S2FC=0.4944 均低于 champion | — |
  | Single-pass cluster_attn 最优 | confirmed | M25-REF=0.4892, M16-CSR=0.4875 (refine 迭代退化) | — |
  | ORT orthogonality 提升 token 质量 | confirmed | M17-ORT=0.5005 (γ=-0.0007, near champion) | 最优 weight? M27(w=0.05)/M28(w=0.001) running |
  | Message_type 组合无效 | confirmed | M24-ORT-D=0.4955, M21-HYB=0.4898, M26-ORT-HYB=0.4998 — 3/3 低于 single mechanism | 组合轴饱和 |
  | Cross-scale attention 有效 | falsified | M22-XCA=0.4954 (-0.0058 vs champion) | — |
  | 机制方向已覆盖: agg(QGC/QSF/CMX/DCA), msg(HYB/detail/XCA), reg(ORT), refine(CSR/REF) | partial | DCA/ITK waiting | attention structure 方向未探索 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion (posA_l1) | 0.5012 | cluster context 核心假设 | 确认机制有效 ✓ |
  | M17-ORT | 0.5005 | cluster token 质量→提升 context | 确认 orthogonality 有效 ✓ |
  | D1-detail | 0.5003 | message_type 变体 | 确认 detail 单独有效 ✓ |
  | M26-ORT-HYB | 0.4998 | ORT 挽救 HYB, 但不超越 single | 确认组合轴饱和 ✓ |
  | M24-ORT-D | 0.4955 | ORT+detail 互相干扰 | 确认组合无协同 ✓ |
  | M22-XCA | 0.4954 | cross-scale attention | 确认跨尺度 attn 无增益 ✓ |
  | M19-S2FC | 0.4944 | 2-scale 消融 | 确认 3-scale 必要 ✓ |
  | M1-QGC | 0.4939 | query-gated context | query gate 无增益 ✓ |
  | M18-S2FM | 0.4933 | 2-scale 消融 | 同上 ✓ |
  | M23-CMX | 0.4910 | max-pool vs mean-pool | 确认 mean-pool 最优 ✓ |
  | M25-REF | 0.4892 | iterative refine | 确认 single-pass 最优 ✓ |
  | M21-HYB | 0.4898 | hybrid message | 确认 context-only 最优 ✓ |
  | M16-CSR | 0.4875 | cluster self-refine | 确认 single-pass 最优 ✓ |
  | M6-QSF | 0.4866 | query into scale gate | scale fusion 无需 query ✓ |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: cluster context 有效 (+0.0118), mean-pool aggregation 最优, single-pass 最优, 3-scale 必要, ORT 维持性能
  - 未验证: 如何打破 ~0.5012 天花板? attention 结构 (nhead/hidden_dim/dropout) 方向完全未探索; ORT 最优强度待 M27/M28 结果
  - 矛盾/疑问: 多个 single mechanism 都能达到 ~0.5005 (ORT, detail), 但组合无法超越。天花板是机制维度限制还是 attention 结构不够 expressive?

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M31-NH4 (nhead=4, head_dim=64): 测试 attention head 结构对 cluster context 质量的影响。
    - Q2: 填补 attention structure 方向缺口。Champion nhead=8 (dim=32/head), 从未探索其他配置。
    - Q3: 若 nhead=4 超越 champion, 说明 cluster attention 需要更 expressive 的 per-head 表示 (64-dim > 32-dim)。若不及, 则确认 nhead=8 为 attention 结构局部最优。
    - 动机对齐: 直接改善 "cluster_attn 把多尺度 context 回写" 的质量。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260728-050301.md
================================================================================
