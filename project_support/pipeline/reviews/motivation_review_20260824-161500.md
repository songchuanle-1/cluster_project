================================================================================
  Motivation Review — cluster_project
  2026-08-24 16:15:00
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
  - check_goal 2026-08-24 16:07:43: Phase 1 NOT YET, continue exploring
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 24h 内无未决 question →
    自主设计允许
  - 触发原因: MFP 轴关闭 (本 tick) + M125 推送后 waiting=4 < 可用卡数5+1=6

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 ≥ 0.005 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012, γ=-0.0544 | 关闭 |
  | decoder 直接访问 cluster tokens (方向①) | partial | DCM=0.5010 (qla 共享通路) > DCA=0.4970 (专用分支) | qia 通路 DCMV running; DUAL 双通路 queued |
  | 多层注入 (方向②) | partial | MLay 2层=0.5010; 3/4/6层重复注入已证退化 (banned) | **{①qla}×{②}=M126 queued; {①qia}×{②} 缺格 → 本次 M136** |
  | MFP (masked feature prediction) | **证伪 (本 tick)** | 3-seed: s1999=0.5020 / s42=0.4869<baseline / s123=0.4960, 均值 0.4950 | 轴关闭, M131/M132 撤回 |
  | encoder-side token 质量轴 (CCL/CGA/BCF/SRL/MEMBANK) | 证伪 | 0.489-0.493 全灭 | 关闭 |
  | CSORT 跨 scale 去相关 | 证伪 | 3/4 seed 负, 0.5020 归因 seed1999 | 关闭 |
  | {qla,qia}×{cluster KV} 2×2 | 进行中 | DCM(qla)=0.5010 ✓, DCMV(qia) running, DUAL queued | M134-DUAL 补格 |
  | DCM seed 稳健性 | 排队中 | DCM 仅 seed1999=0.5010 | M135-DCM-S42 queued |
  | **DCMV (qia) seed 稳健性** | **未验证** | DCMV 仅 seed1999 running (M133) | **本次 M137-DCMV-S42** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|--------------|
  | M119-MFP | 0.5020 | 特征级 mask 重建 aux loss | seed1999 红利确认 (M129/M130 证伪) |
  | M129-MFP-S42 | 0.4869 | MFP seed42 对照 | < baseline, 触发 MFP 关闭 |
  | M130-MFP-S123 | 0.4960 | MFP seed123 对照 | ≤0.498, 完成 3-seed 判定 → 关闭 |
  | M124-DCM | 0.5010 | decoder query 经 qla 共享 KV 读 cluster | decoder-access 轴最优 |
  | M123-DCA | 0.4970 | decoder query 专用分支 cross-attend cluster | 弱于 DCM, 轴内淘汰 |
  | M86-MLAY | 0.5010 | 2层注入 (方向②) | 多层注入有效但平台饱和 |
  | M128-DET-DCM | 0.4990 | detail × DCM | 无正协同, 2×2 满格 |
  | M133-DCMV | running 17/50 | qia 视觉通路 cluster KV (DCM 对称版) | 补 {qla,qia} 缺格 |
  | M125-MLAY-DCA | running (本 tick 推送) | {②}×{①qla 专用分支} | 2×2 {2层}×{DCA} 补格 |
  | M126-MLAY-DCM | waiting | {②}×{①qla 共享} | 2×2 {2层}×{DCM} 补格 |
  | M134-DUAL | waiting | qla+qia 双通路 | {qla,qia}×{cluster KV} 第4格 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); decoder-access 轴 DCM=0.5010 (qla 共享 >
    DCA 专用); 多层注入 MLay=0.5010; MFP 证伪 (本 tick)。
  - 未验证: ① **{①qia×②} 组合缺格** — M126 测 ②×①qla, 但 ②×①qia (MLay×DCMV)
    从未测; ② **DCMV (qia) seed 稳健性** — DCM 有 M135 对照, DCMV 是 decoder-access
    轴 qia 侧唯一缺 seed 证据的机制。
  - MFP 关闭后队列收缩: 原 7 waiting → 4 waiting (M126/M134/M135/M122), 深度不足
    (4 < 容量5+1=6), 需补设计 2 个。
  - 关键洞察: 平台 ~0.501 是 seed-1999 结构上限 (多机制同平台饱和)。破平台依赖
    ①×② 正交组合 (M125/M126 在测) 或通路补格 (M134)。MFP 关闭不改变此判断,
    反而确认 encoder-side aux loss 路线终结, decoder-access + 多层注入是仅存
    两条已验证结构路线。其交叉组合矩阵 {①qla,①qia}×{②} 只剩 MLay×DCMV 一格。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体1 M136-MLAY-DCMV (②×①qia): 2层注入 × qia 视觉通路 cluster KV。
    因果假设: M126 已验证 ②×①qla (排队), DCMV (M133) 正在验证 ①qia 单机制;
    若 decoder-access 收益通路不变 (pathway-invariant), 则 ②×①qia 应与 ②×①qla
    对称 (≈ M126); 若通路不对称, 则揭示 qia/qla 在组合中的差异 — 两种结果都
    推进 {①qla,①qia}×{②} 组合矩阵的最后一格。即使 DCMV 中性, 该格仍判明
    2层注入与 qia 通路无协同 (等价于 MLay)。
  - 变体2 M137-DCMV-S42: DCMV seed=42 对照。
    因果假设: DCM=0.5010 已配 M135-DCM-S42 判稳健性; DCMV 作为对称的 qia 机制,
    seed 稳健性是 decoder-access 轴 qia 侧能否写进论文的硬性缺口。纯 seed 变更,
    与 M135/M120/M129 同型, 不引入新机制。
  - 与 banned[]/constraints 校验:
    - M136: 非 gate/非 langroute/非 attnpool/非 residual/非 true_route/非 3-6层注入;
      零新增参数 (复用 dcmv 的 use_cluster_mem_visual 分支 + cluster_att_num_layers=2);
      不改变数值分布; 无新超参; FLOPs 与 DCM 同量级 ≤10G。
    - M137: 纯 seed 变更 (继承 M135/M120/M129 seed 对照先例), 非调参。
    - 不设计新 seed 以外超参扫描 (Phase1 禁止调参); 不设计 gate 系/encoder token
      质量 (全灭); 不设计 3/4/6 层注入 (banned)。
  - 条件独立性: 两变体均不依赖 DCMV 结果 — M136 在 DCMV 中性时可判定 qla/qia
    通路组合对称性, M137 是纯 seed 对照; 均不依赖 MFP/DCM。保持队列深度。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260824-161500.md
================================================================================
