================================================================================
  Motivation Review — cluster_project
  2026-08-22 17:19:00
================================================================================

## 1. Goal
  - goal.json:
    metric: mIoU ≥ 0.51 on ScanRefer
    description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
    cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'
    假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。"
  - Target: mIoU ≥ 0.5100
  - Champion: M95-CTF-HCG-CSORT = 0.5020 (seed1999 outlier; true mechanism mean ~0.498)
  - Gap: +0.0080 (nominal) / ~+0.012 (vs true mechanism mean)
  - Phase: 1 NOT YET (check_goal 2026-08-22 17:08)
  - Active constraints: Phase 1 禁止调参 (结构性机制变更 only); 突破方向①
    (cluster context 调制 decoder query) 已解锁; 禁 N² attention; 禁 gate系;
    禁 residual系; FLOPs ≤ 10.0G; 分支停止 <0.002 且不升 → 停
  - Active retentions: None (goal.json constraints[] 无"活跃保留"字样;
    decisions 最近 question 20260821-141824 为 GPU7 并发运维问题, 非设计保留)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 有效 | confirmed | A1-A0=+0.0118 | 无需更多验证 |
  | Routing 有害 | confirmed | A3-A1=-0.0544 | 禁止 |
  | CTF+HCG 1层 ~0.501 | confirmed | M81=0.5012, M65=0.5002, M78=0.5008 | 基底确定 |
  | MLay (2层 legacy) ~0.501 | partial | M86=0.5010 | M120/M122 seed 对照运行中 |
  | detail message 独立有效 | confirmed | D1=0.5003 (γ=+0.0109) | M121 组合测试中 |
  | encoder-side token 质量增强 (CCL/CGA/BCF) | disproved | M115=0.4890, M116=0.4926, M117=0.4926 | 轴关闭 |
  | decoder 直接访问 cluster tokens (DCA/DCM) | untested | M123 running, M124 running | M125-M128 排队 |
  | **MFP (masked feature prediction) = 0.5020** | **ambiguous** | M119 tie champion @seed1999 | **需 seed 对照判定机制性** |
  | detail × decoder 访问 2×2 | untested | M127/M128 排队 | 已设计 07:13 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95-CTF-HCG-CSORT | 0.5020 | CSORT 变体, seed1999 outlier | 名义 champion, 归因种子效应 |
  | M81-CTF-HCG | 0.5012 | 核心 CTF+HCG context 机制 | 核心架构 ✓ |
  | M86-MLAY (2层) | 0.5010 | 2层 legacy readback | 隔离 context 深度为核心收益 |
  | D1-detail | 0.5003 | detail message 粒度 | 消息构造轴独立有效 (γ=+0.0109) |
  | M115-CCL | 0.4890 | 对比损失 | 失败, 轴关闭 |
  | M116-CGA | 0.4926 | 簇间图注意力 | 失败, 轴关闭 |
  | M117-BCF | 0.4926 | 双向信息流 | 失败, 轴关闭 |
  | **M119-MFP** | **0.5020** | 特征级 mask 重建辅助损失 | **唯一零伤害 encoder-side 机制, 但 tie 种子效应存疑** |
  | M123-DCA / M124-DCM | — | decoder 侧 cluster 直接访问 | 运行中 (M123 ep2, M124 刚启动) |
  - 关键观察: encoder-side 全部 ~0.501 平台。CCL/CGA/BCF 掉到 0.489-0.493;
    MFP 是唯一不伤的 encoder-side 辅助损失 (0.5020)。但 MFP 用 seed 1999 —
    与 champion M95 同种子, 0.5020 可能同为种子红利。CSORT 前例:
    0.5020@1999 → 3/4 其他 seed 负 (0.4902/0.4940/0.4930) → 轴关闭。

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context-only 有效; CTF+HCG 1层; MLay 2层 (partial); detail message
  - 已证伪: routing / CSORT / ORT / MEMBANK / SRL / CCL / CGA / BCF (encoder-side 质量轴)
  - 已排队: M125-MLAY-DCA, M126-MLAY-DCM, M127-DET-DCA, M128-DET-DCM (decoder 访问
    2×2 满格), M122-MLAY-S123 (seed 对照)
  - 已运行: M123-DCA, M124-DCM, M120-MLAY-S42, M121-DET-MLAY
  - 缺口 (本次):
    * **MFP 机制性未判定**: MFP=0.5020 tie champion 但同 seed 1999。若 MFP-S42/
      S123 也 ~0.50 → MFP 是真实机制 (特征完整性 → context 质量), 可与 decoder
      访问组合; 若掉到 ~0.49 → 同 CSORT, 是种子红利, 关闭 MFP 轴。
    * CSORT 前例是教训: 单 seed tie 不能证明机制, 必须 seed 矩阵验证。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M129-MFP-S42 / M130-MFP-S123**: 复制 ctf_hcg_mfp 包, 仅改 seed=42/123。
    验证假设 "MFP 的 0.5020 是机制性 (特征级 mask 重建提升 cluster token 信息
    完整性) 而非 seed-1999 偶然"。若 S42/S123 ≥0.50 → MFP 真实, 是 encoder-side
    唯一可用机制, 下一步可与 decoder 访问 (DCA/DCM) 组合破 0.501 平台;
    若 <0.495 → MFP 关闭, 聚焦 decoder 访问轴。
  - 这批变体在故事线中的角色: 排除种子效应混淆 (同 CSORT/MLay 的 seed 矩阵
    方法论), 为 "MFP 是否可叠加" 提供因果证据。非调参: seed 改变是验证稳健性,
    无超参/无数值/无结构参数调整 (goal.json 多 seed 对照为常规操作)。
  - 队列深度: waiting=5 < 6 (可用卡5+1), 补 2 个 → 7 ≥ 6。

## 6. Next Batch
  → M129-MFP-S42 + M130-MFP-S123 → 见 pipeline/designs/exp_design_20260822-1719.md
================================================================================
