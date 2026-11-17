================================================================================
  Motivation Review — cluster_project
  2026-08-22 07:13:32
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
  - Phase: 1 NOT YET (check_goal 2026-08-22 07:07)
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
  | MLay (2层 legacy) ~0.501 | confirmed(单seed) | M86=0.5010 | M120/M122 seed 对照运行中 |
  | detail message 独立有效 | confirmed | D1=0.5003 (γ=+0.0109) | M121 组合测试中 |
  | encoder-side token 质量增强 (CCL/CGA/BCF) | disproved | M115=0.4890, M116=0.4926, M117=0.4926 | 轴关闭 |
  | decoder 直接访问 cluster tokens (DCA 专用分支) | untested | M123 排队 | M123 waiting |
  | decoder 共享语言通路读 cluster (DCM) | untested | M124 排队 | M124 waiting |
  | 2层 context 深度 × decoder 访问 (MLay×DCA/DCM) | untested | M125/M126 排队 | 已设计 03:15 |
  | **detail message × decoder 访问** | **UNTESTED** | D1 独立有效但从未与 DCA/DCM 组合 | **本次设计** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M81-CTF-HCG | 0.5012 | 核心 CTF+HCG context 机制 | 核心架构 ✓ |
  | M86-MLAY (2层 legacy) | 0.5010 | 无解相关 2 层 readback | 隔离 context 深度为核心收益 |
  | M95-CTF-HCG-CSORT | 0.5020 | CSORT 变体, seed1999 outlier | 名义 champion, 归因种子效应 |
  | D1-detail | 0.5003 | detail message 粒度 | 消息构造轴独立有效 (γ=+0.0109) |
  | M115-CCL | 0.4890 | 对比损失 | 失败, 轴关闭 |
  | M116-CGA | 0.4926 | 簇间图注意力 | 失败, 轴关闭 |
  | M117-BCF | 0.4926 | 双向信息流 | 失败, 轴关闭 |
  | M123-DCA / M124-DCM | — | decoder 侧 cluster 直接访问 | 排队中 |
  - 关键观察: encoder-side 全部 ~0.501 平台 (包括刚关闭的 CCL/CGA/BCF)。
    writeback 是 `inst_feats + gate*message` 单通道有损和。decoder 直接访问
    cluster tokens 是唯一未测试的结构轴 (DCA/DCM 排队)。detail message 是仅有的
    两个独立有效 encoder-side 机制之一 (另一个是 MLay 2层)。

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context-only 有效; CTF+HCG 1层; MLay 2层 legacy; detail message
  - 已证伪: routing / CSORT / ORT / MEMBANK / SRL / CCL / CGA / BCF (encoder-side 全灭)
  - 已排队: M123-DCA, M124-DCM, M125-MLAY-DCA, M126-MLAY-DCM (decoder 访问 2×2),
    M122-MLAY-S123 (seed 对照)
  - 已运行: M118-LCC (跨模态), M119-MFP (mask 重建), M120-MLAY-S42, M121-MLAY-DET
  - 未验证 (本次):
    * **detail message × decoder 专用分支 (DET×DCA)**: D1-detail 在 writeback 路径上
      独立有效 (0.5003, γ=+0.0109); DCA 让 decoder query 直接 cross-attend cluster
      tokens, 绕过 writeback。组合检验: 若 writeback 有损是瓶颈, decoder 直连后
      detail 是否仍提供增益? 若 detail 收益在 token 内容质量 (消息构造本身),
      则 DET×DCA > DCA; 若 detail 仅通过 writeback 有损路径才重要, 则 ≈DCA。
    * **detail message × decoder 共享通路 (DET×DCM)**: 同一假设经共享语言通路验证,
      完成 2×2 矩阵 {context, detail}×{DCA, DCM} 的第 3/4 格。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M127-DET-DCA**: 验证假设 "decoder 直连 cluster 后, 消息构造质量 (detail vs
    context) 是否仍影响定位精度"。新信息流: cluster 消息 detail 构造 → cluster
    tokens → decoder qca 直连。若 >DCA(context) → detail 收益来自 token 内容质量,
    与访问路径正交可加; 若 ≈DCA → detail 收益已被 decoder 直连吸收 (writeback
    有损才是 detail 的受益通道)。
  - **M128-DET-DCM**: 同一假设经共享通路验证, 完成 {context,detail}×{DCA,DCM} 2×2。
  - 这批变体在故事线中的角色: 系统判定 "消息构造质量 × decoder 访问路径" 交互 —
    若 detail×DCA > DCA 且 > detail, 两条独立有效机制叠加破 0.501 平台;
    若持平, 证明 decoder 直连已覆盖消息构造收益 (判定 writeback 瓶颈归属)。
  - 非调参: 两个变体均为已验证结构机制 (detail message 构造 + decoder cluster
    cross-attention) 的组合, 无新超参, 无数值微调, 新计算图 = decoder qca 读取
    detail 构造的 cluster tokens。

## 6. Next Batch
  → M127-DET-DCA + M128-DET-DCM → 见 pipeline/designs/exp_design_20260822-071332.md
================================================================================
