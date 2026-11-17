================================================================================
  Motivation Review — cluster_project
  2026-08-26 03:11:00
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999,
    归因 seed-1999 红利, 结构真实 mean ~0.498)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-26 03:07:38: Phase 1 NOT YET
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 24h 内无 type=question;
    最近 route_change (08-26 01:10 M134-DUAL 轴关闭) 为已执行决策非保留 → 自主设计允许
  - 触发原因: 队列深度 waiting=5 < 可用卡5+1=6 → 自主补设计 1 个

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 ≥ 0.005 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012, γ=-0.0544 | 关闭 |
  | decoder-access 双通路 {qla,qia}×KV 2×2 | 关闭 | qla=0.5010 ✓ / qia=0.4950 ✗ / DUAL=0.4970 ✗ (M134) | 矩阵补格完成 |
  | {decoder-access, 多层}×{DCA,DCM,DCMV} 叠加 | 关闭 | M125=0.4970 / M126=0.4980 — 通路组合不叠加 | 关闭 |
  | 多层注入 (方向②) | partial | MLay 2层 legacy=0.5010; ctf_hcg 2层=0.4940 (M96) | {②}×{DUAL} 正确格 = M139 queued |
  | MFP / CSORT / token-FFN(CTF) | 证伪 | MFP 3-seed 均值 0.4950; CSORT 归因 seed1999; CTF=0.4995 | 关闭 |
  | **cluster token 实例判别性 (信息瓶颈)** | 未测/待 CLICA | 平台 0.501-0.502 饱和, 通路组合全不叠加 → 瓶颈在 token 信息量 | M140-CLICA queued (本设计区分: 跨尺度一致性) |
  | **多尺度组合的实例一致性 (粗 token 忠实性)** | **未测** | HCG 逐级组合读回, 粗 token 混实例 → 组合 context 被稀释 | **本次设计 M141-CSIC 填补** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|--------------|
  | M134-DUAL (本 tick 前终态) | 0.4970 | {qla,qia} 双通路直读 cluster KV | 补齐 {qla,qia} 2×2 矩阵, qia 轴弱, 双通路不叠加 |
  | M125-MLAY-DCA | 0.4970 | {② legacy}×{DCA} | 组合不叠加, 通路轴关闭 |
  | M124-DCM | 0.5010 | decoder qla 读 cluster | decoder-access 轴最优, 平台饱和 |
  | M86-MLAY | 0.5010 | 2层 legacy 注入 | legacy 2层强基底 |
  | M81-CTF-HCG | 0.5012 | champion 基底 | **champion 结构, 用于 M141 隔离对照** |
  | M140-CLICA | waiting | cluster-instance 对比对齐 loss | token 判别性监督 (与 M141 正交) |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); 通路组合不叠加; MFP/CSORT/CTF 全灭;
    {qla,qia} 双通路矩阵补格完成。
  - 未验证: cluster token 的**信息质量**如何提升。M140-CLICA 从"实例判别性"
    角度下手 (同尺度内分开实例)。
  - **本设计填补的缺口**: 即使 token 判别性 OK (CLICA 方向), **多尺度组合的
    实例一致性**仍未受监督 — 粗尺度 token 由 mean-pool 聚合大区域, 若混多个实例,
    它的内容对各实例都不忠实; HCG 逐级组合读回会把这份"混合 context"注入每个实例。
    → 粗 token 对主导实例的忠实性 (跨尺度一致性) 是独立于判别性的第二个瓶颈假设。
  - 矛盾/疑问: 是否所有 loss 级监督都会像 CLICA 预期那样撞上同一信息墙?
    本设计的价值在于: 若 CLICA 破不了 0.50 平台 (判别性非瓶颈), CSIC 仍是
    一个不同的因果路径 (组合一致性), 两者任一成功都能打开新信息路径。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M141-CTF-HCG-CSIC (Cross-Scale Instance Consistency):
    在 champion ctf_hcg (M81=0.5012, seed 1999) 上增加一个跨尺度实例一致性 loss:
    对每个 GT 实例, 细尺度簇 token 均值应与包含它的粗尺度 token 语义一致 (cosine)。
    粗 token 被监督成对"主导实例"忠实。
  - 因果假设: 多尺度 context 由 HCG 逐级组合读回 (点→l0→l1→l2)。若粗 token
    混实例, 组合后的 context 对每个实例都是稀释的 → 定位 mask 模糊。CSIC 直接
    惩罚粗 token 与主导实例细表示的不一致 → 多尺度 context 实例忠实 → 破 0.50 平台。
  - 为什么是 loss 而非新模块: 与 CLICA 同理由 — 零推理成本, 计算图干净, 复用
    cluster bank 的 build_cluster_feats + cluster_ids_list (已暴露)。
  - 与 CLICA 的区分 (正交性): CLICA = 同尺度内实例**判别** (InfoNCE, 有正负对);
    CSIC = 跨尺度实例**一致** (cosine 拉近, 无负样本, 不同尺度间)。判别 ≠ 一致:
    即使每尺度 token 可区分实例, 粗/细尺度对同一实例的看法仍可能矛盾。
  - 与 banned[]/constraints 校验:
    - 非 gate/非 langroute/非 attnpool/非 residual/非 true_route/非 3-6层注入/非调参。
    - 新 loss = 新计算图 (新梯度路径进 cluster token), 非数值配置 → 通过 Phase 1.6。
    - 超参: λ=0.1 (辅助 loss, 与 sem_loss weight[6]=0.1、CLICA 0.1 同量级; 可消融 0/0.1/1.0)。
    - FLOPs: 仅 ~328 token 的 cosine 计算, 可忽略 → ≤10G 约束满足。
    - 零新增参数 → 峰值显存无增量。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260826-0311.md
================================================================================
