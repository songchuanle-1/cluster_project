================================================================================
  Motivation Review — cluster_project
  2026-08-16 02:15:25
================================================================================

## 1. Goal
  - pipeline/goal.json:
    - target: mIoU ≥ 0.5100 (ScanRefer)
    - description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
      cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'
      假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51"
    - baseline: model_base1 = 0.4894
    - champion: model_base1_quard2_c2f_enc_lite_posA_l1 = 0.5012 (seed 1999, done_complete)
    - gap: +0.0088 → Phase 1 NOT YET (check_goal 2026-08-16 02:07)
  - 当前 phase: 1 (continue exploring, champion 未达 target)
  - 活跃保留检查: goal.json constraints[] 无未解除"活跃保留"条款; decisions 近24h 无
    route_change/question 保留 (08-15 10:12 route_change 已闭环 ORT 轴并保留 M97/M98
    证据点, 非设计保留) → 自主设计允许。

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1 posA_l1 0.5012 vs base 0.4894 (γ=+0.0118) | 无 |
  | 显式 routing 有效 | falsified | A3 true_route 0.4468 (γ=-0.0544) | 无 (已定案) |
  | seed 方差 ~±0.004-0.007 | confirmed (08-14) | M90 CTF×HCG s123=0.4940, M91 HCG s42=0.4963 | champion 自身跨 seed 验证中 (M99/M100/M101) |
  | ORT (尺度内正交) 多样性破顶 | falsified/narrowing | M92 CTF×HCG×ORT=0.4930, M94 HCG×ORT=0.4930 (γ=-0.0082) | M97-CHAMP-ORT 最后证据点 |
  | CSORT (跨尺度正交) 多样性破顶 | **partial — 首个 >champion 信号** | M95 CTF×HCG×CSORT **0.5020** (running, seed1999, 21/50, no_impr=9/10) | **跨 seed 未验证** ← 本次设计核心 |
  | 多层注入 (MLAY) 破顶 | in-progress | M86 running (0.4580@ep7), M96 CTF×HCG×2LAY running (0.4680@ep8) | 待终态 |
  | QMOD query 调制 | falsified | M85 0.4930, M88 0.4930 | 无 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | A1 champion (seed1999) | 0.5012 | context 回写 | 核心证据 ✓ |
  | M81 CTF×HCG (seed1999) | 0.5012 | token质量×正确交付 | tie champion |
  | M95 CTF×HCG×CSORT (seed1999) | **0.5020** running | 在 tie 机制上加跨尺度正交 | **首个高于 champion 的观察** |
  | M89 CTF×HCG seed42 | 0.4980 (本tick早停) | 同机制 seed42 | 掉 0.0032 vs M81 → seed 敏感 |
  | M90 CTF×HCG seed123 | 0.4940 | 同机制 seed123 | 掉 0.0072 → 复现性存疑 |
  | M92 CTF×HCG×ORT | 0.4930 | 三轴 ORT | 反降 → ORT 轴收窄 |
  | M94 HCG×ORT | 0.4930 | ORT 单基底 | 与 M92 同值 → ORT 独立有害 |
  | M91 HCG seed42 | 0.4963 | HCG seed 复现 | 掉 0.0039 → seed 敏感 |
  (来源: pipeline/analyses/ 2026-08-14~16 + experiments.csv + monitor 2026-08-16 02:07)

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (γ=+0.0118); routing 证伪; ORT 多样性轴在强基底上无害/有害。
  - 已验证: seed 方差 ~±0.004-0.007 — M89 (s42)=0.4980 / M90 (s123)=0.4940 / M91 (s42)=0.4963
    对 M81/M65 的 seed1999 高分构成系统性掉点。
  - **新信号**: M95 (CTF×HCG×CSORT, seed1999) = 0.5020, 第一个 > champion 0.5012 的观察。
    但 0.5020 vs 0.5012 仅 +0.0008, **在 seed 方差 ±0.004-0.007 之内** — 单点无法区分
    "CSORT 真破顶" vs "seed1999 有利性", 且 M95 no_impr=9/10 即将早停, 该值很可能就是终值。
  - 核心缺口: **CSORT 机制缺乏同 seed 对照**。CTF×HCG 本身已有 s42=0.4980 (M89)、
    s1999=0.5012 (M81)、s2026 (M102 待跑) 三点; 但 CTF×HCG×CSORT 只有 seed1999 单点。
    无法回答: CSORT 的 +0.0008 是机制收益还是 seed 运气?
  - 矛盾/疑问: 若 CSORT 真有效, 应在 s42/s2026 上也维持相对 CTF×HCG 的同 seed 增量;
    若 0.5020 是 seed 有利, s42/s2026 的 CSORT 会跌回 ~0.494-0.498 且无一致增量。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M103-CTF-HCG-CSORT-S2026: CTF×HCG×CSORT seed=2026 — 与 M102 (CTF×HCG s2026)
    构成同 seed 对, 直接测 CSORT 在 s2026 的增量 (M103 vs M102 同 seed, 单一变量 CSORT)。
  - 变体 M104-CTF-HCG-CSORT-S42: CTF×HCG×CSORT seed=42 — 与 M89 (CTF×HCG s42=0.4980,
    已终态) 构成同 seed 对, 直接测 CSORT 在 s42 的增量 (M104 vs M89 同 seed, 单一变量)。
  - 预期 (若 CSORT 真有效): M103 ≈ M102 + ~0.001-0.003, M104 ≈ 0.499-0.501 (均高于
    M89 0.4980 同 seed 基线); 若 seed 有利: M103/M104 无一致增量, 甚至跌回 ~0.494-0.498。
  - 角色: 排除/确认 "M95 0.5020 是 CSORT 机制收益" 假说 — 把 CSORT 从单点观测变成
    3 seed × 2 config 的完整矩阵 (s1999: M81 0.5012 vs M95 0.5020; s2026: M102 vs M103;
    s42: M89 0.4980 vs M104)。同 seed 对照把 seed 方差从机制判读中剥离, 这是故事线
    判定 CSORT 是否真破顶的最干净设计。
  - 无冲突: 不改结构 (与 M95 相同 cluster_mode=ctf_hcg_csort, csort_weight=0.01),
    仅 seed 变更; 不违反 banned[] (非 gate/route/residual/调参); 通过 Phase 1.6
    (复现性对照, 与 M89-M102 同性质)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260816-021525.md
================================================================================
