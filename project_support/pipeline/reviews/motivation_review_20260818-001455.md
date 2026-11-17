================================================================================
  Motivation Review — cluster_project
  2026-08-18 00:14:55
================================================================================

## 1. Goal
  - pipeline/goal.json:
    - target: mIoU ≥ 0.5100 (ScanRefer)
    - description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
      cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'
      假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51"
    - baseline: model_base1 = 0.4894
    - champion: M95-CTF-HCG-CSORT = 0.5020 (check_goal 2026-08-18 00:07)
    - gap: +0.0080 → Phase 1 NOT YET (continue exploring)
  - 活跃保留检查 (Phase 0.5 双源):
    ① goal.json constraints[] — 无未解除"活跃保留"条款 (FLOPs/禁调参/分支停止等常规条款;
       【已解除·用户 08-10】指向前两方向, 非设计保留)
    ② decisions/_index.md 近 10 条 — 均为 skip_design/terminal/queue_push/early_stop,
       无未闭环 route_change/question; 近 24h 无 type=question
      → 自主设计允许

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1 0.5012 vs base 0.4894 (γ=+0.0118) | 无 |
  | 显式 routing 有效 | falsified | A3 0.4468 (γ=-0.0544) | 无 |
  | seed 方差 ~±0.004-0.007 | confirmed | M99(s42)=0.4930, M100(s123)=0.4980, M102/M101(s2026)=0.4920 | 无 |
  | ORT (尺度内正交) 破顶 | falsified | M92/M94=0.4930; M97-CHAMP-ORT running (最后证据点) | 无 |
  | 多层注入破顶 | falsified | M96 2LAY=0.4940 退化; M86-MLAY running | 无 |
  | QMOD query 调制 | falsified | M85/M88=0.4930 | 无 |
  | **CSORT (token 侧跨尺度正交) 破顶** | **partial — 首个>champion 信号** | M95 CTF×HCG×CSORT **0.5020** (+0.0008, seed1999) | 跨 seed 验证进行中 (M98/M103-M108) |
  | **readback message 侧冗余是否残余瓶颈** | **untested** | M95 只去相关 token 源侧, 目标侧 (per-point 消息) 未处理 | 本批填补 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95 CTF×HCG×CSORT (s1999) | 0.5020 | 首个>champion 的 CSORT 观测 (token 侧相邻尺度去相关) | 破顶候选信号 |
  | M81 CTF×HCG (s1999) | 0.5012 | token质量×正确交付 tie champion | 核心基线 |
  | M89 CTF×HCG s42 | 0.4980 | 同机制 seed42 | 掉 0.0032 → seed 敏感 |
  | M90 CTF×HCG s123 | 0.4940 | 同机制 seed123 | 掉 0.0072 → 最弱 seed |
  | M92/M94 ORT | 0.4930 | ORT 三轴/单基底 (尺度内正交) | ORT 轴收窄 |
  | M96 CTF×HCG×2LAY | 0.4940 | 多层注入 | 2 层退化, 方向关闭 |
  | M99 champion s42 | 0.4930 | champion 基底 seed42 | champion 跨 seed 波动 -0.009 |
  | M100 champion s123 | 0.4980 | champion 基底 seed123 | champion 跨 seed 波动 -0.003 |
  | M102/M101 s2026 | 0.4920 | 第三 seed 判读校准点 | 方差上界收紧 |
  | M103-M108 CSORT 矩阵 | waiting/running | CSORT 跨 seed 验证 | queued |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; routing 证伪; ORT 收窄; 多层注入关闭; QMOD 证伪;
    champion 基底 seed 方差 0.4920-0.5012 (±0.008) 确认。
  - **核心未验证 A**: CSORT 在 champion 基底/CTF×HCG 基底的跨 seed 增量 —
    8 格矩阵 (M98/M103-M108) 已在队, 本 tick 无需重复。
  - **核心未验证 B (新)**: M95 CSORT 只去相关 **cluster token (源侧)** 的相邻尺度
    冗余, 但 readback 是经 **learned level_gate 融合 per-scale 消息**后写回 inst_feats
    (目标侧)。即使 token 已去相关, 融合时 gate 可重新引入目标侧冗余 — "readback 冗余
    是 0.5012 平台的残余瓶颈" (CTF 分析结论) 从未在消息侧直接测试。
  - 若 message 侧冗余确为瓶颈 → 目标侧去相关应 > token 侧去相关 → 突破 0.5020。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M109-CSORT-MSG (csort_msg): 把 cross-scale orth penalty 移到 **readback
    message** (每点从各尺度 gather 到的 context 消息), 直接去相关目标侧冗余。
    与 M95 构成"去相关目标轴"2 格消融 (M81 无 loss / M95 token 侧 / M109 message 侧),
    同基底 (CTF×HCG)、同 seed (1999)、同权重 (0.01), 唯一变量是 loss 作用对象
    (token vs message)。零新增参数, 新 loss 计算图。
  - 预期推进: 若 M109 > M95 (>0.5020) → message 侧冗余是残余瓶颈, 去相关目标侧
    正确, 故事线从"token 多样性"升级为"readback 消息互补性"; 若 M109 ≤ M95 →
    token 侧已充分去相关, 0.5012 平台瓶颈不在目标侧冗余, 排除该假设 (排除也是推进)。
  - 无冲突: 新 loss 计算图 (per-point 消息对 abs-cosine), 非数值调参, 非 gate 系,
    非 routing 系, 非 residual 系; 通过 Phase 1.6 (见 exp_design §8)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260818-001455.md
================================================================================
