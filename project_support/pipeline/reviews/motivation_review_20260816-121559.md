================================================================================
  Motivation Review — cluster_project
  2026-08-16 12:15:59
================================================================================

## 1. Goal
  - pipeline/goal.json:
    - target: mIoU ≥ 0.5100 (ScanRefer)
    - description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
      cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'
      假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51"
    - baseline: model_base1 = 0.4894
    - champion: M95-CTF-HCG-CSORT = 0.5020 (check_goal 2026-08-16 12:07)
    - gap: +0.0080 → Phase 1 NOT YET (continue exploring)
  - 活跃保留检查 (Phase 0.5 双源):
    ① goal.json constraints[] — 无未解除"活跃保留"条款 (仅 FLOPs/禁调参/分支停止等常规条款)
    ② decisions/_index.md 近 10 条 route_change/question — 08-15 10:12 route_change 已闭环
      ORT 轴并保留 M97/M98 证据点 (非设计保留); 近 24h 无 type=question → 自主设计允许

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1 0.5012 vs base 0.4894 (γ=+0.0118) | 无 |
  | 显式 routing 有效 | falsified | A3 0.4468 (γ=-0.0544) | 无 |
  | seed 方差 ~±0.004-0.007 | confirmed | M89(s42)=0.4980, M90(s123)=0.4940, M91(s42)=0.4963 | champion 自身跨 seed 验证中 (M99/M100/M101) |
  | ORT (尺度内正交) 破顶 | falsified/narrowing | M92/M94=0.4930 | M97-CHAMP-ORT 最后证据点 (running) |
  | **CSORT (跨尺度正交) 破顶** | **partial — 首个>champion 信号** | M95 CTF×HCG×CSORT **0.5020** (+0.0008, seed1999) | **跨 seed 验证缺口** |
  | 多层注入破顶 | falsified | M96 CTF×HCG×2LAY=0.4940 (2层退化), M86 running | 已 ban 3/4/6 层, 方向关闭 |
  | QMOD query 调制 | falsified | M85=0.4930, M88=0.4930 | 无 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95 CTF×HCG×CSORT (s1999) | 0.5020 | 首个>champion 的 CSORT 观测 | 破顶候选信号 |
  | M81 CTF×HCG (s1999) | 0.5012 | token质量×正确交付 tie champion | 核心基线 |
  | M89 CTF×HCG s42 | 0.4980 | 同机制 seed42 | 掉 0.0032 → seed 敏感 |
  | M90 CTF×HCG s123 | 0.4940 | 同机制 seed123 | 掉 0.0072 → 最弱 seed |
  | M92/M94 ORT | 0.4930 | ORT 三轴/单基底 | ORT 轴收窄 |
  | M96 CTF×HCG×2LAY | 0.4940 | 多层注入 | 2 层退化, 方向关闭 |
  | M99/M100 champion s42/s123 | running | champion 跨 seed 基线 | 判读基准 (in progress) |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; routing 证伪; ORT 收窄; 多层注入关闭; QMOD 证伪。
  - **核心未验证**: CSORT 的 +0.0008 是机制收益还是 seed1999 有利性 — 需要跨 seed 同 seed 对照。
  - **矩阵缺口**:
    ① CTF×HCG×CSORT 已有 s1999(0.5020)/s2026(M103 queued)/s42(M104 queued), **缺 s123**
       (与 M90 CTF×HCG s123=0.4940 构成同 seed 对, 测 CSORT 在最弱 seed 的增量)
    ② champion-base CSORT (M98, s1999) 仅 1 个 seed, **缺跨 seed 验证** (与 M99 champion
       s42 running 构成同 seed 对, 测 champion 基底上 CSORT 独立增量)
  - 若同 seed 增量一致为正 → CSORT 成立; 若无 → 0.5020 归因 seed1999, 故事线回到 0.5012 上限。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M105-CTF-HCG-CSORT-S123: 填 CSORT 矩阵最弱 seed 格 — 与已终态 M90 (CTF×HCG
    s123=0.4940) 同 seed 对照, 直接测 CSORT 在方差最大处的增量。若 M105 > 0.4940 明显,
    说明 CSORT 在最不利 seed 仍正向 → 机制证据增强。
  - 变体 M106-CHAMP-CSORT-S42: 补 champion-base CSORT 第二 seed 点 — 与 running 的
    M99 (champion s42) 同 seed 对照, 测 CSORT 独立于 CTF×HCG 基底在 champion 上的增量。
    与 M98 (champion-base CSORT s1999) 构成 champion-base CSORT 的 2-seed 验证。
  - 无冲突: 不改结构/超参, 仅 seed 变更 (与 M89-M104 同性质复现性对照); 通过 Phase 1.6
    (非数值调参, 假说明确, 直接测 CSORT 机制增量)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260816-121559.md
================================================================================
