================================================================================
  Motivation Review — cluster_project
  2026-08-14 21:25:00
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
  | **seed 方差** | **本 tick 确认** | M91-HCG-R2 (seed42) 0.4963 vs M65 (seed1999) 0.5002 掉 0.0039; M90 (seed123) 0.4940 掉 0.0072 | 0.5012 含 seed1999 有利性 |
  | 尺度内多样性 (ORT) | 梯度断流已修, champion 基底从未真测 | M17 0.5005 伪信号; M62 0.4979 在 DRP 基底 | M97-CHAMP-ORT 队列中 |
  | **跨尺度多样性 (CSORT)** | **从未在 champion 基底测** | M95 (CTF×HCG 基底) 队列中 | **M98-CHAMP-CSORT 本 tick 设计** |
  | CONS/QMOD/CCP 一致性系 | falsified | 0.483-0.495 | 排除 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion (A1) | 0.5012 | context 回写有效 | 核心假设 ✓ |
  | M91-HCG-R2 (seed42) | 0.4963 | HCG 复现检查掉 0.0039 | **确认 seed 方差** ⚠ |
  | M90-CTF-HCG-S3 (seed123) | 0.4940 | CTF×HCG 复现检查掉 0.0072 | 复现性存疑 ⚠ |
  | M17-ORT | 0.5005 | 曾归因 ORT — 现证伪(梯度断流) | ORT 轴从未真测 |
  | M81-CTF-HCG | 0.5012 | 正协同 (seed1999) | 待 M89 定区间 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); CTF/CTF×HCG 在 seed1999 达 champion 水平;
    **seed 方差 ~±0.004-0.007 (本 tick M91 确认)**
  - 未验证:
    ① 尺度内多样性 (ORT) 在 champion 基底真实贡献 → M97-CHAMP-ORT 队列中
    ② **跨尺度多样性 (CSORT) 在 champion 基底真实贡献 → 本 tick 缺口** —
       M95-CSORT 只在 CTF×HCG 基底, 有 seed 复现性混淆; 与 M97 平行地, 需要
       champion 基底 CSORT 做干净的单变量对照
    ③ CTF×HCG seed42 复现 (M89 running)
  - 矛盾/疑问: seed 方差确认后, "破顶"标准应从严 — 任何变体需在 seed1999 上 > 0.5012
    且最好跨 seed 验证; 0.5012 本身可能就是 seed 有利值。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M98-CHAMP-CSORT: 填补 gap ② — 复制 champ_ort 包 → champ_csort, 把尺度内 ORT loss
    换成跨尺度 CSORT loss (粗 token ⊥ 细子簇聚合), 在**与 champion 完全同基**的
    C2F_ClusterAttn_Lite 上施加。单变量对照 champion 0.5012, 与 M97-CHAMP-ORT 构成
    多样性轴的 2×2 (尺度内/跨尺度 × champion 基底) 干净网格。
  - Q3: 若 M97/M98 任一 > 0.5012 → 多样性轴破顶, 组合实验 (M92/M94/M95) 按新基准解释;
    若双持平 → 佐证 0.5012 为 seed1999 架构天花板, 多样性轴闭环, 转 M96-2LAY 结果。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260814-2125.md
================================================================================
