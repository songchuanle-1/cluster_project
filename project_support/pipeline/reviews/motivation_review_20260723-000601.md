================================================================================
  Motivation Review — cluster_project
  2026-07-23 00:06:01
================================================================================

## 1. Goal
  - Target: mIoU ≥ 0.5100 | Champion: model_base1_quard2_c2f_enc_lite_posA_l1 0.5012 | Gap: +0.0088
  - Motivation: "multi-scale cluster context — cluster bank aggregates point cloud features → cluster_attn writes multi-scale context back to inst_feats → improves localization accuracy"
  - Routing claim falsified (A3=0.4468); benefit comes from context, not routing.

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 cluster context 提升定位 | confirmed | posA_l1 0.5012 vs base 0.4894 (γ=+0.0118) | 机制消融待 Phase 2 |
  | 3-scale 均必要 | confirmed | M18-S2FM(2-scale) 0.4933 < 0.5012, M19-S2FC 0.4944 < 0.5012 | 等 M19 完成后形式化 |
  | cluster routing 有独立收益 | falsified | A3=0.4468 (−0.0544), A4-shuffle=0.4941 | — |
  | detail message type 有效 | plausible | D1-detail 0.5003 (距 champion −0.0009), stopped_unknown | M20-DET clean rerun 确认 |
  | context+detail 互补 | unverified | — | M21-HYB 在队列 |
  | cross-scale info exchange 提升表达 | unverified | — | **本批设计目标** |
  | orthogonality regularization 有效 | unverified | — | M17-ORT 刚启动 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | posA_l1 (champion) | 0.5012 | 核心: 3-scale cluster context | 确认 multi-scale context 有效 ✓ |
  | D1-detail | 0.5003 | detail message 变体, 接近 champion | 证明 detail 单独有效, 值得 rerun |
  | C1-layerscale | 0.4998 | gate 机制, stopped_unknown | gate 系失败, 加入 banned |
  | B5-residual | 0.4944 | residual refine 变体 | residual 上限 ~0.4944, 加入 banned |
  | M19-S2FC | 0.4944 | scale ablation (drop medium) | 证明 medium scale 必要 (in progress) |
  | A4-shuffle | 0.4941 | shuffle control for routing | 证明 routing 无益, context 是主因 |
  | M1-QGC | 0.4939 | query-gated context | gate 又失败, 确认 gate 方向不可行 |
  | M18-S2FM | 0.4933 | scale ablation (drop coarse) | 证明 coarse scale 不可替代 |
  | C3-refine | 0.4931 | refine mechanism | refine 低于 champion, 非关键 |
  | M16-CSR | 0.4875 | cluster self-refine | << baseline, 方向失败 |
  | M6-QSF | 0.4866 | query进尺度融合gate | gate 方向再失败 |
  | A3-true_route | 0.4468 | routing 生效 | 证伪 routing 假设 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: multi-scale context 有效 (γ=+0.0118), 3-scale 均必要, routing 无益
  - 未验证: 
    1. cross-scale information exchange — cluster tokens 在 3 个 scale 之间目前是独立的, 没有信息交互
    2. detail message type 稳定性 — M20-DET 在 queue
    3. context+detail 互补 — M21-HYB 在 queue
    4. orthogonality regularization — M17-ORT 刚启动
  - 矛盾/疑问: 为什么 D1-detail 0.5003 接近 champion 但 stopped_unknown? 当前 champion 已达 plateaus 还是仍有上升空间?

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M22-XCA (Cross-scale Cluster Attention)**: 
    - 填补缺口: cluster tokens 在不同 scale 间独立运作, 无信息交互
    - 动机: coarse [8] 捕获全局 context, fine [256] 捕获局部 detail — 交叉注意力可让两者互补
    - 实现: 在 build_cluster_feats 之后, 将所有 scale 的 cluster tokens concat, 过一个 self-attention + FFN, 再 split 回各 scale
    - 预期: > champion 0.5012 (cross-scale 信息 enrichment)
    - 失败也推进: 证明独立 scale 已足够, cross-talk 无益
  - 不与 banned[] 冲突: 不是 gate, 不是 routing, 不是 residual, 不是 N² attention on points (仅 cluster tokens 间)

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260723-000601.md
================================================================================
