================================================================================
  Motivation Review — cluster_project
  2026-08-22 03:15:00
================================================================================

## 1. Goal
  - goal.json:
    metric: mIoU ≥ 0.51 on ScanRefer
    description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
    cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'
    假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。"
  - Target: mIoU ≥ 0.5100
  - Champion: M95-CTF-HCG-CSORT = 0.5020 (seed1999 outlier; true mean ~0.498)
  - Gap: +0.0080 (nominal) / ~+0.012 (vs true mechanism mean)
  - Phase: 1 NOT YET (check_goal 2026-08-22 03:07)
  - Active constraints: Phase 1 禁止调参 (结构性机制变更 only); 突破方向①
    (cluster context 调制 decoder query) 已解锁; 禁 N² attention; 禁 gate系;
    禁 residual系; FLOPs ≤ 10.0G; 分支停止 <0.002 且不升 → 停
  - Active retentions: None (goal.json constraints[] 无"活跃保留"字样;
    decisions 最近 route_change/question — 20260821-141824 为 GPU7 并发问题非设计保留)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 有效 | confirmed | A1-A0=+0.0118 | 无需更多验证 |
  | Routing 有害 | confirmed | A3-A1=-0.0544 | 禁止 |
  | CTF+HCG 1层 ~0.501 | confirmed | M81=0.5012, M65=0.5002, M78=0.5008 | 基底确定 |
  | MLay (2层 legacy) ~0.501 | confirmed(单seed) | M86=0.5010 | M120/M122 seed 对照运行中 |
  | detail message 独立有效 | confirmed | D1=0.5003 (γ=+0.0109) | M121 组合测试中 |
  | encoder-side token 质量增强 (CCL/CGA/BCF) | disproved | M115=0.4890, M116=0.4926, M117=0.4926 | 轴关闭 |
  | decoder 直接访问 cluster tokens (DCA 专用分支) | untested | M123 排队 | M123 waiting |
  | decoder 共享语言通路读 cluster (DCM) | untested | M124 排队 | M124 waiting |
  | **2层 context 深度 × decoder 直接访问** | **UNTESTED** | 两个独立有效机制未组合 | **本次设计** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M81-CTF-HCG | 0.5012 | 核心 CTF+HCG context 机制 | 核心架构 ✓ |
  | M86-MLAY (2层 legacy) | 0.5010 | 无解相关 2 层 readback | 隔离 context 深度为核心收益 |
  | M95-CTF-HCG-CSORT | 0.5020 | CSORT 变体, seed1999 outlier | 名义 champion, 归因种子效应 |
  | D1-detail | 0.5003 | detail message 粒度 | 消息构造轴独立有效 |
  | M115-CCL | 0.4890 | 对比损失 | 失败, 轴关闭 |
  | M116-CGA | 0.4926 | 簇间图注意力 | 失败, 轴关闭 |
  | M117-BCF | 0.4926 | 双向信息流 | 失败, 轴关闭 |
  | M123-DCA / M124-DCM | — | decoder 侧 cluster 直接访问 | 排队中 |
  - 关键观察: encoder-side 全部 ~0.501 平台 (包括刚关闭的 CCL/CGA/BCF)。
    writeback 是 `inst_feats + gate*message` 单通道有损和。decoder 直接访问
    cluster tokens 是唯一未测试的结构轴 (DCA/DCM 排队)。MLay(2层) 与 detail
    是仅有的两个独立有效 encoder-side 机制。

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context-only 有效; CTF+HCG 1层; MLay 2层 legacy; detail message
  - 已证伪: routing / CSORT / ORT / MEMBANK / SRL / CCL / CGA / BCF (encoder-side 全灭)
  - 已排队: M123-DCA (decoder 专用分支), M124-DCM (decoder 共享通路), M122-MLAY-S123
  - 已运行: M118-LCC (跨模态), M119-MFP (mask 重建), M120-MLAY-S42, M121-MLAY-DET
  - 未验证 (本次):
    * **2层 context 深度 × decoder 专用分支 (MLay×DCA)**: M86 证明 2层 legacy 单达
      0.5010, M123-DCA 测试 decoder 直连。两者是独立轴 (encoder context 深度 vs
      decoder 读取路径)。组合测试: 若 writeback 是瓶颈, decoder 直连叠加 2层 context
      应 > 各自单独; 若两轴冗余, 组合 ≈ 最强单轴。
    * **2层 context 深度 × decoder 共享通路 (MLay×DCM)**: 同上, 但通过共享语言通路。
      完成 2×2 矩阵 {1层,2层}×{DCA,DCM} — 系统判定 context 深度与 decoder 访问方式
      是否交互。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M125-MLAY-DCA**: 验证假设 "context 深度与 decoder 直接访问是独立可加轴"。
    decoder qca 建立在 2层 legacy 精炼的 inst_feats 之上 — 新信息流: 2层 context
    回写 → cluster tokens → decoder qca。若 >0.501 → 两轴正交可加, 破板;
    若 ≈0.501 → 两轴冗余, decoder 直连已包含 context 深度收益。
  - **M126-MLAY-DCM**: 验证同一假设通过共享语言通路是否成立。与 M125 形成
    2×2 矩阵第 4 格, 若 DCA/DCM 任一崩溃, 另一提供兜底证据。
  - 这批变体在故事线中的角色: 组合已证独立有效的两个机制, 系统探索
    "context 深度 × decoder 访问方式" 交互空间 — 是破 0.501 平台的最直接一步。
  - 非调参: 两个变体均为两个已存在结构机制的组合, 无新超参, 无数值微调,
    新计算图 = decoder qca 作用于 2层精炼 context。

## 6. Next Batch
  → M125-MLAY-DCA + M126-MLAY-DCM → 见 pipeline/designs/exp_design_20260822-0315.md
================================================================================
