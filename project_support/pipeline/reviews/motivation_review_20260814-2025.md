================================================================================
  Motivation Review — cluster_project
  2026-08-14 20:25:00
================================================================================

## 1. Goal
  - pipeline/goal.json: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: model_base1_quard2_c2f_enc_lite_posA_l1 0.5012 | Gap: +0.0088
  - Phase 1: NOT YET — continue exploring
  - 约束(本 tick 复核): Phase1 禁止调参只允许结构性机制变更; 禁 gate系/语言路由/attnpool/qcond/agg/multi/prune/3-4-6层重复注入/大型QKV/true_route/residual; FLOPs≤10G; 禁止单变体改 schedule

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写提升定位 | confirmed | A1 0.5012 vs base 0.4894 (γ=+0.0118) | 需确认哪些设计必要 |
  | Routing 提升特征表达 | falsified | A3 true_route 0.4468, γ=-0.0544 | 已排除 |
  | Token 质量 (CTF FFN) | confirmed | M41-CTF 0.4995, γ=+0.0101 | 单轴未破顶 |
  | 正确多尺度交付 (HCG) | confirmed | M65-HCG 0.5002, γ=+0.0108 | 必要修复, 本身不破顶 |
  | CTF×HCG 正协同 | **复现性存疑 (本 tick)** | M81 (seed1999) 0.5012 tie champion; M90 (seed123) 0.4940 -0.0072 | M89/M91 (seed42) 待终态 |
  | ORT token 多样性 | 梯度断流已修, champion 基底从未真测 | M17-ORT 0.5005 是 broken-loss 伪信号; M62-ORTG 0.4979 在 DRP 基底 | **champion 基底固定 ORT 空白** |
  | 跨尺度多样性 (CSORT) | 未测 | M95 队列中 (CTF×HCG 基底) | champion 基底 CSORT 需 HCG 结构, 不独立 |
  | CONS/QMOD/CCP 一致性系 | falsified | 0.483-0.495 | 排除 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion (A1) | 0.5012 | context 回写有效 | 核心假设 ✓ |
  | M90-CTF-HCG-S3 (seed123) | 0.4940 | CTF×HCG 复现检查掉 0.0072 | 复现性存疑 ⚠ |
  | M17-ORT | 0.5005 | 曾归因 ORT — 现证伪(梯度断流) | ORT 轴从未真测 |
  | M62-ORTG | 0.4979 | 真梯度 ORT 在 DRP 基底 | DRP 基底非 champion |
  | M81-CTF-HCG | 0.5012 | 正协同 (seed1999) | 待 seed 验证 |
  | M65-HCG | 0.5002 | 正确交付 | 必要修复 ✓ |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; CTF/CTF×HCG 在 seed1999 下达 champion 水平
  - 未验证:
    ① **ORT 多样性在 champion 基底的真实贡献** — M17 是 broken-loss, M62 在 DRP 基底,
       M92/M94 在 HCG 基底; champion 基底 (C2F_ClusterAttn_Lite) + 修复版 ORT 从未跑过。
       ortg 包的 'ort' 模式 (C2F_ClusterAttn_ORT, 与 champion 同基) 已实现且从未启用。
    ② CTF×HCG 复现区间 (M89/M91 待终态)
  - 矛盾/疑问: M17-ORT 0.5005 在梯度完全断流下仍达 0.5005 — 说明该收益非 ORT 机制所致,
    反而可能暗示 champion 架构本身在 seed1999 下普遍 ~0.5005-0.5012。多样性轴真实价值成谜。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M97-CHAMP-ORT: 填补 gap ① — ortg 包 C2F_ClusterAttn_ORT (extends C2F_ClusterAttn_Lite,
    与 champion 完全同基) + cluster_mode='ort', 首次在 champion 基底上真实施压修复版
    正交 loss。单变量对照 champion 0.5012, 直接回答"多样性轴是否破顶关键"。
    M17-ORT 的 0.5005 伪信号被排除后, 这是该轴第一次有效证据。
  - Q3: 若 M97 > 0.5012 → 多样性轴破顶, 与 M92/M94 (HCG 基底) 一起构成 2×2 网格
    (champion/HCG × ORT); 若持平 → champion 架构接近天花板, 转向已入队的 M95-CSORT/
    M96-2LAY 结果解释。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260814-2025.md
================================================================================
