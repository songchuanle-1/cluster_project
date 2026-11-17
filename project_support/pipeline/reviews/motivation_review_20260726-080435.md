================================================================================
  Motivation Review — cluster_project
  2026-07-26 08:04:35
================================================================================

## 1. Goal
  - pipeline/goal.json: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: posA_l1 0.5012 | Gap: +0.0088

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 cluster context 提升定位精度 | confirmed | posA_l1 0.5012 vs base 0.4894 (γ=+0.0118) | 如何突破 0.5012 天花板? |
  | Orthogonality regularization 提升 cluster diversity | confirmed | M17-ORT 0.5005 (γ=+0.0111), 持平 champion | orth_weight 敏感性未探索 |
  | Detail message 有效 | confirmed | D1-detail 0.5003 (γ=+0.0109) | 与 ORT 组合(M24-ORT-D running) |
  | Hybrid context+detail 协同 | refuted | M21-HYB 0.4898 (γ=+0.0004) | 组合方向关闭 |
  | Routing 有效 | refuted | A3-true_route 0.4468 (γ=-0.0544) | A4-shuffle 确认结构注入也有损 |
  | Cross-scale attention 有益 | partial | M22-XCA 0.4954 (+0.0060), 但不及 champion | 收益有限 |
  | 3-scale 均必要 | confirmed | M18-S2FM 0.4933, M19-S2FC 0.4944 | 消融完毕 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | posA_l1 (champion) | 0.5012 | 直接验证 cluster context 机制 | 确认核心假设 ✓ |
  | M17-ORT | 0.5005 | 验证 orthogonality 提升 cluster diversity | 确认 ORT 机制有效 ✓ |
  | D1-detail | 0.5003 | 验证 alternative message formulation | 确认 detail 独立有效 ✓ |
  | M21-HYB | 0.4898 | 验证 context+detail 组合 | 证伪组合协同 ✗ |
  | M22-XCA | 0.4954 | 验证跨尺度 cluster 交互 | 单独收益不足 |
  | M18-S2FM | 0.4933 | 消融 coarse scale | 确认 3-scale 必要 |
  | M16-CSR | 0.4875 | 验证 cluster self-refine | 单机制无效 |
  | A4-shuffle | 0.4941 | routing 控制组 | 确认 routing 方向关闭 |
  | M1-QGC | 0.4939 | query-gated context | 收益有限 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 注入有效, ORT 有效(但仅持平 champion), detail 独立有效
  - 未验证: 
    1. ORT orth_weight 敏感性 — 0.01 是否最优? 更强/更弱的 orthogonality 能否突破?
    2. ORT+detail 组合效果 (M24-ORT-D running)
    3. refine mode 效果 (M25-REF waiting)
    4. max-pool aggregation 效果 (M23-CMX running)
  - 矛盾/疑问: ORT=0.5005 与 champion=0.5012 持平未超越, 是否 orth_weight 不够强? 或 ORT 已触天花板?

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M27-ORT-W5 (orth_weight=0.05): 验证 "更强的 orthogonality 能否突破 champion"
    Q1缺口: ORT 机制虽有效但未超越 champion — 可能是 orth_weight 不够
    预期: 若 >0.5012 → ORT 是突破路径; 若 <0.5005 → 0.01 已是最优
  - M28-ORT-W1 (orth_weight=0.001): 验证 "极弱 orthogonality 是否足够"
    Q1缺口: ORT 机制的 sensitivity 完全未知
    预期: 若 >0.5005 → 弱正则化更优; 若 <0.5005 → 需要≥0.01 的正则化强度
  - 故事推进: ORT 敏感性曲线建立 → 指导后续 ORT+detail/ORT+refine 的最优组合配置
  - 均为 config-only 变更(复用 model_base1_quard2_c2f_enc_lite_posA_l1_ort 模型包), 零代码风险

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260726-080435.md
================================================================================
