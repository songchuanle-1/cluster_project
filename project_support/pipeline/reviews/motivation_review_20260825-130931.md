================================================================================
  Motivation Review — cluster_project
  2026-08-25 13:09:31
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999,
    CSORT 轴已关闭, 0.5020 归因 seed-1999 红利, 结构真实 mean ~0.498)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-25 13:07:37: Phase 1 NOT YET, continue exploring
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 24h 内无未决 question;
    最近 route_change (08-24 16:13 MFP 轴关闭) 为已执行决策非保留 → 自主设计允许
  - 触发原因: M134 推送后 waiting=5 < 容量5+1=6 (cluster_project 容量=5)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 ≥ 0.005 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012, γ=-0.0544 | 关闭 |
  | decoder 直接访问 cluster tokens (方向①) | partial | DCM(qla)=0.5010 > DCA=0.4970; DCMV(qia)=0.4950 弱 | DUAL 双通路 (M134 running) |
  | 多层注入 (方向②) | partial | **MLay 2层 legacy=0.5010; ctf_hcg 2层=0.4940 退化 (M96)** | **{② legacy}×{qla}=M126 已终态; {②}×{DUAL}=M138 用错 base!** |
  | **{② legacy}×{DUAL} 满强度组合** | **未测** | — | **本次设计 M139 (修正 M138 base)** |
  | MFP (masked feature prediction) | 证伪 | 3-seed 0.5020/0.4869/0.4960, 均值 0.4950 | 轴关闭 |
  | CSORT 跨 scale 去相关 | 证伪 | 3/4 seed 负, 0.5020 归因 seed1999 | 关闭 |
  | {qla,qia}×{cluster KV} 2×2 | 补格中 | qla=0.5010 ✓ / qia=0.4950 ✗ / DUAL=M134 running | M134 补第4格 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|--------------|
  | M126-MLAY-DCM (本 tick 终态) | 0.4980 | {② legacy 2层}×{DCM qla 共享 KV} | **组合不叠加**: 0.4980 < 两组分 (M86=0.5010, M124=0.5010) — 2层注入与 decoder qla 访问共享同一信息瓶颈 |
  | M133-DCMV | 0.4950 | qia 视觉通路 cluster KV 直读 | qia 单轴弱 (-0.0060 vs DCM) |
  | M124-DCM | 0.5010 | decoder query 经 qla 读 cluster | decoder-access 轴最优, 平台饱和 |
  | M86-MLAY | 0.5010 | 2层 legacy 注入 (方向②) | **legacy 2层是强基底** (关键: ctf_hcg 2层退化) |
  | M96-CTF-HCG-2LAY | 0.4940 | ctf_hcg 模式 2层 | **ctf_hcg 2层退化** — M86 分析已修正: 退化是 ctf_hcg 模式特有, 非多层注入本身 |
  | M125-MLAY-DCA | running 0.4970 | {② legacy}×{DCA 专用分支} | 同 M126, 预计不叠加 |
  | M134-DUAL | running | qla+qia 双通路 (1层) | {qla,qia} 双通路叠加 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); DCM qla=0.5010 (decoder-access 轴最优);
    MLay 2层 legacy=0.5010 (多层注入有效); MFP/CSORT/encoder-token 全灭。
  - M126 新证据: {② legacy 2层}×{DCM qla} = 0.4980 — **组合不叠加**, 两机制共享瓶颈。
  - **设计缺陷发现**: M138-MLAY-DUAL (queued) config 用 `cluster_mode: ctf_hcg`,
    但 M86 分析已证明 **ctf_hcg 2层退化 (M96=0.4940), legacy 2层才是强基底 (M86=0.5010)**。
    M138 作为"满强度组合天花板格"测试, 建在退化的 ctf_hcg base 上 → 结果会误导故事线。
  - **未验证核心缺口**: {② legacy 2层}×{DUAL 双通路} 满强度组合 — 用正确的 legacy base。
    若破 0.502 → 故事闭环; 若 ≈0.501 → 确认平台饱和, 组合不叠加。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M139-MLAY-DUAL-LEGACY: **修正 M138 的 cluster_mode 为 legacy** —
    legacy 2层 (C2F_ClusterAttn_Lite, M86 强基底) × 双通路 (use_cluster_mem qla +
    use_cluster_mem_visual qia)。cluster_att_num_layers=2, seed=1999。
  - 因果假设: 方向① 最优 DCM(qla)=0.5010 与方向② 最优 legacy-MLay=0.5010 各自有效;
    M126 证明 {② legacy}×{单通路 qla} 不叠加。满强度 {② legacy}×{双通路 DUAL} 是
    组合空间最后未测格 — 且必须用 legacy base (ctf_hcg 2层退化会污染结果)。
  - 与 M138 的关系: M138 用 ctf_hcg base (可能因 M96 退化而失败), M139 用 legacy base,
    两者构成 base-mode 消融对 — 若 M138 失败但 M139 成功, 直接证明 ctf_hcg 2层退化
    而非组合本身无效。M139 是故事线正确的天花板格。
  - 与 banned[]/constraints 校验:
    - 非 gate 系/非 langroute/非 attnpool/非 residual/非 true_route/非 3-6层注入
      (2层 legacy = M86 已验证档位, 非重复注入); 非调参 (零新超参, 复用已验证结构标志)。
    - cluster_mode 变更 (ctf_hcg→legacy) 是新计算图结构选择, 非数值调整 — 通过 Phase 1.6
      调参气味检测 (新信息交互路径: Cluster_Attn_Lite 的 coarse-to-fine 级联 readback)。
    - FLOPs 与 M86/M138 同量级, ≤10G 约束满足。
  - 条件独立性: 不依赖 M126/M134/M136/M138 结果 — 直接回答 legacy 满强度组合问题。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260825-130931.md
================================================================================
