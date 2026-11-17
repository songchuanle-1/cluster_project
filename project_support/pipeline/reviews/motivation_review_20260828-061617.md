================================================================================
  Motivation Review — cluster_project
  2026-08-28 06:12:00
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999,
    跨 seed mean ~0.495)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-28 06:07:36: Phase 1 NOT YET
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 近 24h 无 type=question;
    最近 route_change 均为已执行决策非保留 → 自主设计允许
  - 触发原因: M143 推送后 waiting=4 < 容量4+1=5 → 自主补设计 1 个

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012 | 关闭 |
  | cluster token 结构变换 (FFN/交互/池化/融合) | 全灭 | C2C/CSF/FLM/pool/TrueRoute | 关闭 |
  | 通路组合叠加 (delivery×delivery) | 关闭 | M125/M126/M134/M136/M138/M139 6次不叠加 | 关闭 |
  | 多层注入 (ctf_hcg@2) | 证伪 | M96-CTF-HCG-2LAY=0.4940 | HCG@2 有害 |
  | **legacy 2层注入 (MLay)** | **有效** | **M86-MLAY=0.5010** (γ=+0.0116) | **与 CSORT 组合未测** |
  | 判别性 loss (CLICA) | 饱和 | M140=0.4970 < base 0.5012 | 判别轴无增益 |
  | 跨尺度一致 loss (CSIC) | 饱和 | **M141=0.4960 (本 tick 终态)** | 一致轴无增益 |
  | CSORT 应用位置 (token vs message) | 非关键 | M109-CSORT-MSG=0.5010 ≈ M95 | 位置轴关闭 |
  | **CSORT (cross-scale orth)** | **champion** | **M95=0.5020** | 唯一破 0.5012 机制 |
  | CSORT × detail 组合 | 检验中 | M146 queued | 去相关×残差回写 |
  | **CSORT × MLay legacy@2 组合** | **未测** | **本次设计 M147** | 去相关×2层注入 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|--------------|
  | M95-CTF-HCG-CSORT (champion) | 0.5020 | 跨尺度 orth 破平台 | 唯一破 0.5012 机制 (seed 脆弱) |
  | M86-MLAY (legacy 2层) | 0.5010 | 2层注入有效 | 结构深度轴独立有效 |
  | M96-CTF-HCG-2LAY | 0.4940 | HCG@2 有害 | 区分 legacy@2 与 HCG@2 |
  | M140-CLICA (本 tick 前一实验) | 0.4970 | 判别性 loss | 判别轴饱和 |
  | **M141-CSIC (本 tick 终态)** | **0.4960** | **跨尺度一致 loss** | **一致轴饱和, loss 监督轴 2 连败** |
  | D1-detail (message_type=detail) | 0.5003 | 残差回写 message | detail 单独有效 |
  | M139-MLAY-DUAL-LEGACY | 0.4880 | 组合轴天花板格 | 组合轴第 5/6 次确认不叠加 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; 结构变换全灭; delivery×delivery 组合不叠加 (6 次);
    HCG@2 有害但 legacy@2 有效 (0.5010); loss 监督轴 (判别 CLICA + 一致 CSIC) 2 连败;
    CSORT 位置非关键。
  - 未验证: **champion 的 cross-scale orth (CSORT=0.5020) 与 legacy 2层注入
    (MLay=0.5010) 是否叠加**。这是两个独立有效的 top 机制: CSORT 在 cluster token
    输入侧去相关 (正则化), MLay 在 encoder 结构侧 2 层注入 (架构深度)。两者位点
    正交, 从未在 legacy base 上组合。
  - 矛盾/疑问: 组合轴已 6 次不叠加, 但那些是 {delivery 机制 × delivery 机制} 的
    同类结构组合; CSORT×MLay 是 {正则化 loss} × {架构深度} 的跨类组合, 与失败
    组合不属同类。且 MLay 是唯一未被 CSORT 污染的独立有效结构机制 (champion
    用 ctf_hcg_csort, MLay 用 legacy Lite)。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M147-MLAY-CSORT: 以 mlay 包 (cluster_mode='legacy', cluster_att_num_layers=2)
    为基础, 在 cluster_att forward 中加入 CSORT cross-scale orth loss
    (csort_weight=0.01, 沿用 champion), 其余完全一致。
  - 因果假设: CSORT 使粗 token 与细子簇聚合去相关 → 各尺度 context 互补; MLay
    2 层 legacy 注入让 encoder 两层都利用互补 context 回写 → 信息容量更大 →
    定位更准 → 破 0.5020。一句话: "去相关的多尺度 context 经 2 层注入 → 信息更富
    → 定位更准"。
  - 与 banned[]/constraints 校验:
    - 非 gate系/语言路由系/attnpool/residual 系; 非 true_route (CSORT 是 loss 不是
      routing 注入); 非 3/4/6 层重复注入 (legacy@2=0.5010 已证有效, 与 banned 的
      "3/4/6 层重复注入已证退化"不同 — banned 指 HCG 3/4/6 层, MLay legacy 2 层
      单独已验证有效)。
    - 非调参: csort_weight=0.01 沿用 champion 已验证值, cluster_att_num_layers=2
      沿用 MLay 已验证值, 无新数值配置; 新 loss 是结构变更 (新计算图/新优化目标),
      符合 Phase 1 结构性机制变更要求。种子 1999 结构首筛。
    - FLOPs/显存: csort loss 仅 (8×64+64×256) 对级 abs-cosine, 2 层注入已实测
      ≤10G → 约束满足。
    - 与"分支停止: 提升<0.002"约束: 若 M147 增益 <0.002 → CSORT×MLay 组合格关闭。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260828-061617.md
================================================================================
