================================================================================
  Motivation Review — cluster_project
  2026-08-15 08:16:00
================================================================================

## 1. Goal
  - pipeline/goal.json:
    - target: mIoU ≥ 0.5100 (ScanRefer)
    - description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
      cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'
      假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51"
    - baseline: model_base1 = 0.4894
    - champion: model_base1_quard2_c2f_enc_lite_posA_l1 = 0.5012 (seed 1999, done_complete)
    - gap: +0.0088 → Phase 1 NOT YET (check_goal 2026-08-15 08:07)
  - 当前 phase: 1 (continue exploring, champion 未达 target)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1 posA_l1 0.5012 vs A0 base 0.4894 (γ=+0.0118) | 无 |
  | 显式 routing 有效 | falsified | A3 true_route 0.4468 (γ=-0.0544 vs A1) | 无 (route_change 08-14 已定案) |
  | CTF (token 质量) 有效 | partial | M41-CTF 0.4995, M81-CTF×HCG 0.5012 tie | seed1999 有利性需澄清 |
  | HCG (正确交付) 有效 | partial | M65-HCG 0.5002, M78-REAGG×HCG 0.5008 | seed1999 有利性需澄清 |
  | seed 方差 ~±0.004-0.007 | confirmed (08-14) | M90-CTF×HCG seed123=0.4940, M91-HCG seed42=0.4963 | **champion 自身跨 seed 未验证** |
  | ORT/CSORT 多样性轴破顶 | untested | M97/M98 queued, M92/M94/M95 各基底 | champion 基底参照缺失 |
  | 多层注入 (MLAY) 破顶 | partial | M86 running (ep5 0.4370), M88-QMOD×MLAY=0.4930 无协同 | M96 组合待跑 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | A1 champion (seed1999) | 0.5012 | 直接验证 context 回写 | 核心证据 ✓ |
  | M90-CTF-HCG-S3 (seed123) | 0.4940 | 同机制不同 seed | **掉 0.0072 → 复现性存疑** |
  | M91-HCG-R2 (seed42) | 0.4963 | 同机制不同 seed | **掉 0.0039 → 复现性存疑** |
  | M93-CTF-SEF | 0.4910 | SE 通道注意力附加 | 失败, gate 族禁区 +1 |
  | M87-DET-CONS | 0.4930 | detail × consistency | 失败, 约束系无破顶 |
  | M81-CTF-HCG (seed1999) | 0.5012 | token质量×正确交付 | tie champion |
  | M84-DET-CTF-HCG | 0.4990 | detail×强基底 | 无正协同 |
  | M65-HCG (seed1999) | 0.5002 | 正确多尺度交付 | 距 champion 0.0010 |
  (来源: pipeline/analyses/ 2026-08-10 ~ 2026-08-15 + experiments.csv)

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (γ=+0.0118); routing 证伪; CTF/HCG 在 seed1999 达 champion-tie。
  - 已验证 (08-14): **seed 方差 ~±0.004-0.007 属实** — 同一机制换 seed 掉点明显。
  - 未验证: **champion (posA_l1) 自身在 seed≠1999 的真实水平**。M90/M91 只验证了
    CTF×HCG / HCG 变体的跨 seed 表现, 从未验证 champion 本身。
  - 矛盾/疑问: 若 champion 自身 seed42/123 也掉到 ~0.494-0.497, 则 0.5012 是
    seed1999 有利值, M97/M98 (champion 基底) 需按更低的 champion 真实水平解读;
    若 champion 跨 seed 稳定 ~0.501, 则 seed 方差主要来自变体而非 champion 基底,
    M97/M98 直接对照 0.5012 成立。
  - **这是当前最高优先级缺口**: 08-14 route_change 已定"破顶需 ≥0.005 且最好跨 seed
    验证", 但 champion 自身无跨 seed 数据 → 任何 champion 基底实验 (M97/M98) 的
    判读都缺少关键对照。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M99-CHAMP-S42: 复制 champion config + seed=42 → 建立 champion 在 seed42 的真实水平。
    填补"champion 自身复现性"证据缺口, 是 M97/M98 (champion 基底多样性) 判读的必要对照。
  - 变体 M100-CHAMP-S123: 复制 champion config + seed=123 → 建立 champion 在 seed123 的水平,
    与 S42 合起来给出 champion 的 seed 方差区间 (与 M90/M91 的 123/42 对应)。
  - 预期: 若 champion seed42/123 ≈ 0.494-0.500 → 证实 0.5012 含 seed1999 有利性,
    champion 真实水平 ~0.497-0.501, M97/M98 破顶标准按真实水平下调;
    若 ≈0.501 → seed 方差主要来自变体, champion 基底稳定。
  - 角色: 排除/确认 "0.5012 为 seed 有利值" 假说 → 校准整个多样性轴判读标准。
  - 无冲突: 不改结构 (仅 seed), 不违反 banned[] (非 gate/route/residual/调参), 
    通过 Phase 1.6 (非数值调参, 是复现性对照 — 与 M89/M90/M91 同性质)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260815-0816.md
================================================================================
