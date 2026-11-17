================================================================================
  Motivation Review — cluster_project
  2026-07-27 05:03:01
================================================================================

## 1. Goal
  - pipeline/goal.json:
    Target: mIoU ≥ 0.5100
    Champion: model_base1_quard2_c2f_enc_lite_posA_l1 (0.5012)
    Description: "多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度"
  - Current: Phase 1 NOT YET, gap=+0.0088

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 cluster context 有效 | confirmed | champion 0.5012 vs base 0.4894 (γ=+0.0118) | — |
  | Orthogonality regularization 提升 cluster diversity | confirmed | M17-ORT 0.5005 vs base 0.4894 (γ=+0.0111), Δchampion=-0.0007 | ORT weight sweep 结果待定 (M27/M28 queued) |
  | detail message_type 独立有效 | confirmed | D1-detail 0.5003 vs base (γ=+0.0109) | — |
  | message_type 维度组合有协同 | **falsified** | HYB=0.4898, E4=0.4944, ORT-D=0.4955 — 全部低于各自单独机制 | 组合方向关闭 |
  | max-pool aggregation 有效 | **falsified** | CMX=0.4910, γ=+0.0016 < 0.002 threshold | — |
  | cross-scale attention 有效 | partial | XCA=0.4954, +0.0060 vs base, 但距 champion -0.0058 | 单独收益不够 |
  | refine 迭代机制有效 | unknown | M25-REF ep9 0.4753 (too early) | 等待终态 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  对最近终态实验:
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | posA_l1 (champion) | 0.5012 | 验证核心 context 注入 | 基准线 ✓ |
  | M17-ORT | 0.5005 | ORT 提升 cluster bank 多样性 | 几乎持平 champion ✓ |
  | D1-detail | 0.5003 | detail message 单独有效 | 独立机制 confirmed ✓ |
  | M24-ORT-D | 0.4955 | ORT+detail 组合 → 退化 | 组合失效 confirmed ✗ |
  | M21-HYB | 0.4898 | context+detail hybrid → 退化 | 组合失效 ✗ |
  | M22-XCA | 0.4954 | cross-scale attention | 有效但不足 ~ |
  | M23-CMX | 0.4910 | max-pool → 退化 | 排除 max-pool ✗ |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context injection (champion), ORT regularization, detail message_type
  - 未验证: ORT weight sweep (M27/M28 queued), refine mechanism (M25-REF running), ORT+refine combination potential
  - 矛盾/疑问: message_type 维度组合 3/3 失败 — 机制冲突是 domain-specific 还是普遍规律？
  - 新缺口: cluster aggregation strategy — mean 是否最优？CMX(max)失败, 但 dual(mean+max) 未试

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M29-DCA: mean+max dual-branch cluster aggregation
    - 填补缺口: aggregation strategy exploration
    - 假设: mean 保留分布信息 + max 保留显著特征 → 互补信息 → 比纯 mean 更丰富的 cluster token
    - 若成功: 开启 aggregation 方向（attention pooling, learned weights 等后续探索）
    - 若失败: 关闭 aggregation 方向，确认 mean 最优
    - 约束校验: ✓ FLOPs (Linear(2C,C) ~131K params, <10.0G), ✓ 不改 schedule, ✓ 非 gate系/route系/residual系
    - vs banned: NOT in banned list

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260727-050301.md
================================================================================
