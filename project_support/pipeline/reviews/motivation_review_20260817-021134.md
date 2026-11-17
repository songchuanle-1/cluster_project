================================================================================
  Motivation Review — cluster_project
  2026-08-17 02:11:34
================================================================================

## 1. Goal
  - pipeline/goal.json:
    - target: mIoU ≥ 0.5100 (ScanRefer)
    - description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
      cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'
      假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51"
    - baseline: model_base1 = 0.4894
    - champion: M95-CTF-HCG-CSORT = 0.5020 (check_goal 2026-08-17 02:07)
    - gap: +0.0080 → Phase 1 NOT YET (continue exploring)
  - 活跃保留检查 (Phase 0.5 双源):
    ① goal.json constraints[] — 无未解除"活跃保留"条款 (FLOPs/禁调参/分支停止等常规条款)
    ② decisions/_index.md 近 10 条 route_change/question — 最近为 08-15 10:12 route_change
      已闭环 (ORT 轴失败, 保留 M97/M98 为证据点, 非设计保留); 近 24h 无 type=question
      → 自主设计允许

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1 0.5012 vs base 0.4894 (γ=+0.0118) | 无 |
  | 显式 routing 有效 | falsified | A3 0.4468 (γ=-0.0544) | 无 |
  | seed 方差 ~±0.004-0.007 | confirmed | M99(s42)=0.4930, M100(s123)=0.4980, M91(s42)=0.4963 | champion s2026 (M101 running) 补齐中 |
  | ORT (尺度内正交) 破顶 | falsified | M92/M94=0.4930; M97-CHAMP-ORT running (最后证据点) | 无 |
  | 多层注入破顶 | falsified | M96 2LAY=0.4940 退化; 已 ban 3/4/6 层 | 无 |
  | QMOD query 调制 | falsified | M85/M88=0.4930 | 无 |
  | **CSORT (跨尺度正交) 破顶** | **partial — 首个>champion 信号** | M95 CTF×HCG×CSORT **0.5020** (+0.0008, seed1999) | **跨 seed 验证进行中** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95 CTF×HCG×CSORT (s1999) | 0.5020 | 首个>champion 的 CSORT 观测 | 破顶候选信号 |
  | M81 CTF×HCG (s1999) | 0.5012 | token质量×正确交付 tie champion | 核心基线 |
  | M89 CTF×HCG s42 | 0.4980 | 同机制 seed42 | 掉 0.0032 → seed 敏感 |
  | M90 CTF×HCG s123 | 0.4940 | 同机制 seed123 | 掉 0.0072 → 最弱 seed |
  | M92/M94 ORT | 0.4930 | ORT 三轴/单基底 | ORT 轴收窄 |
  | M96 CTF×HCG×2LAY | 0.4940 | 多层注入 | 2 层退化, 方向关闭 |
  | M99 champion s42 | 0.4930 | champion 基底 seed42 | champion 跨 seed 波动 -0.009 |
  | M100 champion s123 | 0.4980 | champion 基底 seed123 | champion 跨 seed 波动 -0.003 |
  | M101/M102 champion/CTF×HCG s2026 | running | 第三 seed 判读校准点 | in progress |
  | M103-M106 CSORT 矩阵 | waiting | CSORT 跨 seed 验证 | queued |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; routing 证伪; ORT 收窄; 多层注入关闭; QMOD 证伪;
    champion 基底 seed 方差 0.4930-0.5012 (±0.008) 确认。
  - **核心未验证**: CSORT 在 champion 基底上是否提供 seed-鲁棒的独立增量 —
    M98(s1999)/M106(s42) 已在队, 但 **s123/s2026 格缺失**, champion-base CSORT
    矩阵 (对照 champion 基底 M99/M100/M101) 无法闭环。
  - **矩阵缺口**:
    ① champion-base CSORT s123 — 与 M100 (champion s123=0.4980) 同 seed 对照, 测 CSORT
      在 champion 基底、方差中位 seed 的增量;
    ② champion-base CSORT s2026 — 与 running 的 M101 (champion s2026) 同 seed 对照,
      测 CSORT 在 champion 基底、第三独立 seed 的增量。
  - 若 CSORT 在 champion 基底 4-seed 同 seed 增量一致为正 → CSORT 为真实机制, 与
    CTF×HCG 的组合判定成立; 若无 → 0.5020 归因 seed1999, 故事线回到 0.5012 上限,
    需另觅结构性机制。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M107-CHAMP-CSORT-S123: 填 champion-base CSORT 矩阵 s123 格 — 与已终态 M100
    (champion s123=0.4980) 同 seed 对照, 直接测 CSORT 独立于 CTF×HCG 基底在 champion
    上的增量。与 M98(s1999)/M106(s42) 构成 3-seed 验证。
  - 变体 M108-CHAMP-CSORT-S2026: 填 champion-base CSORT 矩阵 s2026 格 — 与 running 的
    M101 (champion s2026) 同 seed 对照, 补齐第 4 个独立 seed 点, 使 champion-base
    CSORT 判定矩阵完整 (4 seed)。
  - 预期推进: 4-seed 同 seed 对照闭环后, CSORT 机制真伪定案; 若成立, champion 栈
    升级为 posA_l1 + CSORT, 再设计下一步破顶机制; 若不成立, 立即转向新结构性机制。
  - 无冲突: 不改结构/超参, 仅 seed 变更 (与 M89-M106 同性质复现性对照); 通过 Phase 1.6
    (非数值调参, 假说明确, 直接测 CSORT 机制增量)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260817-021134.md
================================================================================
