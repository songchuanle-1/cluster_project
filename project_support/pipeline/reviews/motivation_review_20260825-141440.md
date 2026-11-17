================================================================================
  Motivation Review — cluster_project
  2026-08-25 14:14:40
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
  - check_goal 2026-08-25 14:07:38: Phase 1 NOT YET, continue exploring
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 24h 内无未决 question;
    最近 route_change (08-24 16:13 MFP 轴关闭) 为已执行决策非保留 → 自主设计允许
  - 触发原因: M135 推送后 waiting=5 ≤ 容量5+1? → 5 < 6, 深度不足触发自主补设计 1 个

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 ≥ 0.005 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012, γ=-0.0544 | 关闭 |
  | decoder 直接访问 cluster tokens (方向①) | partial→**关闭组合** | DCM(qla)=0.5010 单独有效; **{DCA,DCM}xMLay 组合不叠加** (M125=0.4970, M126=0.4980) | 组合轴已关闭 |
  | 多层注入 (方向②) | partial | MLay 2层 legacy=0.5010; ctf_hcg 2层=0.4940 退化 (M96) | {②}×{DUAL} 正确格 = M139 queued |
  | **cluster token 实例判别性 (信息瓶颈)** | **未测** | 平台 0.501-0.502 饱和, 所有读/写通路组合不叠加 → 瓶颈在 token 自身信息量 | **本次设计 M140 填补** |
  | {qla,qia}×{cluster KV} 2×2 | 补格中 | qla=0.5010 ✓ / qia=0.4950 ✗ / DUAL=M134 running | M134 补第4格 |
  | MFP / CSORT / token-FFN(CTF) | 证伪 | 3-seed 均值 0.4950; CSORT 归因 seed1999; CTF=0.4995 | 关闭 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|--------------|
  | M125-MLAY-DCA (本 tick 终态) | 0.4970 | {② legacy 2层}×{DCA qia 专用分支} | **组合不叠加** — 与 M126 一起关闭 decoder-access × MLay 轴 |
  | M126-MLAY-DCM (昨 tick 终态) | 0.4980 | {② legacy 2层}×{DCM qla 共享 KV} | 组合不叠加, 两机制共享信息瓶颈 |
  | M124-DCM | 0.5010 | decoder qla 读 cluster | decoder-access 轴最优, 平台饱和 |
  | M86-MLAY | 0.5010 | 2层 legacy 注入 (方向②) | legacy 2层是强基底 (ctf_hcg 2层退化) |
  | M81-CTF-HCG | 0.5012 | champion 基底 | **champion 结构, 用于 M140 隔离对照** |
  | M133-DCMV | 0.4950 | qia 视觉通路 cluster KV 直读 | qia 单轴弱 |
  | M134-DUAL | running | qla+qia 双通路 (1层) | {qla,qia} 双通路叠加, 待定 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); DCM qla=0.5010; MLay 2层 legacy=0.5010;
    MFP/CSORT/CTF token-FFN 全灭。
  - 新证据 (本 tick M125 + 昨 tick M126): **所有"增加读取/回写通路"的机制组合都
    不叠加** — DCM/DCA/DCMV × MLay 全部 ≤0.498。这说明瓶颈**不在通路数量**,
    而在 **cluster token 自身携带的信息量**: mean-pool 聚合的 cluster token
    丢失了实例判别性 → 无论多少条通路去读/写, 拿到的都是同一份有限 context。
  - 核心未验证假设: **若 cluster token 被监督成实例可判别 (encode instance
    identity), context 回写质量提升 → 突破 0.50-0.502 平台?**
  - 矛盾/疑问: 通道 (通路) 轴已探尽; token 质量轴 CTF (per-token FFN) 试过但
    失败 (0.4995) — 但 CTF 只做了非线性变换, 没有引入**实例级监督信号**。
    本设计不是再加一层, 而是给 token 一个判别目标。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M140-CTF-HCG-CLICA (CLuster Instance Contrastive Alignment):
    在 champion 基底 ctf_hcg (M81=0.5012, seed 1999) 上, 增加一个 cluster-instance
    对比对齐损失: 训练时用 GT 实例标签给每个 cluster token 打标 (多数投票),
    拉近同实例 cluster token, 推开不同实例 cluster token (InfoNCE)。
  - 因果假设: cluster token 目前是 mean-pool 聚合 → 实例判别性弱 → 回写 context
    通用化。对比损失直接优化 cluster token 的实例判别性 → 回写携带实例信息 →
    定位精度提升。
  - 为什么是 loss 而非新模块: 已有 sem_align 对比损失 (query↔text) 验证了
    对比训练在该框架有效 (contrastive_align_loss=True 是标配); cluster-instance
    对齐是同一范式在 cluster bank 上的应用, 零新增推理模块, 计算图干净。
  - 为什么用 champion ctf_hcg base: 隔离对照 — champion 0.5012 vs champion+clica,
    单一变量。若 γ ≥ +0.003 → 机制有效, 是打破平台的第一条新信息路径;
    若 ≈0 → 平台不是 token 判别性瓶颈, 需范式级新方向。
  - 与 banned[]/constraints 校验:
    - 非 gate/非 langroute/非 attnpool/非 residual/非 true_route/非 3-6层注入/非调参。
    - 新 loss = 新计算图 (新梯度路径进 cluster token), 非数值配置 → 通过 Phase 1.6。
    - 超参: τ=0.1 (对比损失标准量级, 参考 sem_align 的 0.07), λ=0.1 (辅助损失,
      与本模型 loss_weight[6]=0.1 的 sem_loss 同量级; 明确声明可消融 0/0.1/1.0)。
    - FLOPs: 对比损失仅 328 个 token 的 cosine 相似度, 可忽略 → ≤10G 约束满足。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260825-141440.md
================================================================================
