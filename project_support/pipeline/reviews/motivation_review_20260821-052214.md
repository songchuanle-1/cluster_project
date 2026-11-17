================================================================================
  Motivation Review — cluster_project
  2026-08-21 05:22:14
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
  - Phase: 1 NOT YET (check_goal 2026-08-21 05:07)
  - Active constraints: Phase 1 禁止调参; 突破方向①(cluster context 调制 decoder query)
    已解锁(用户 08-10); 禁 N² attention; 禁 gate系
  - Active retentions: None (constraints[] 无"活跃保留"字样; 最近 10 条决策无
    route_change/question — 双源检查通过)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 有效 | confirmed | A1-A0=+0.0118 | 无需更多验证 |
  | Routing 有害 | confirmed | A3-A1=-0.0544 | 禁止 |
  | CTF+HCG 1层 ~0.501 | confirmed | M81=0.5012, M65=0.5002, M78=0.5008 | 基底确定 |
  | MLay (2层 legacy) 达 champion | confirmed (单 seed) | M86=0.5010 | seed 稳健性 (M120/M122) |
  | CSORT / ORT / MEMBANK / SRL | disproved | 多 seed 负增益 | 轴关闭 |
  | CCL/CGA/BCF/LCC/MFP 新机制批次 | WAITING | M115-M119 | 等运行结果 |
  | **decoder 直接访问 cluster tokens** | **UNTESTED** | 所有机制均 encoder-side | **本次设计** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M81-CTF-HCG | 0.5012 | 核心 CTF+HCG context 机制 | 核心架构 ✓ |
  | M86-MLAY (2层) | 0.5010 | 无解相关 2 层 readback | 隔离 context 深度为核心收益 |
  | M95-CTF-HCG-CSORT | 0.5020 | CSORT 变体, seed1999 outlier | 名义 champion, 归因种子效应 |
  | M109-CSORT-MSG | 0.5010 | message 级 decorrelation | 与 M81 持平 |
  | M110-MEMBANK / M111-SRL | 0.4954/0.4912 | 跨 batch 记忆 / 空间重建 loss | 失败, 轴关闭 |
  | M85-QMOD | 0.4930 | 突破方向① decoder query 调制(gate 实现) | 失败 — 但为 gate, 非结构注意力 |
  | M44-CSF / M22-XCA | 0.4958/0.4954 | 跨 scale cluster 交互 | 失败, 轴关闭 |
  - **关键观察**: ~0.501 平台横跨所有 encoder-side 机制 (CSORT/ORT/detail/MLay/MEMBANK-S123),
    无一触及 decoder 侧。writeback 是 `inst_feats + gate*message` 的单通道有损和,
    decoder 只看到 inst_feats, 多尺度 cluster tokens 从未被 decoder 直接读取。

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context-only 有效; CTF+HCG 1层 ~0.501; MLay 2层 legacy ~0.501
  - 已排队 (M115-M119): CCL/CGA/BCF/LCC/MFP — 全部 encoder-side (cluster token 表示/交互)
  - 已运行 (M120/M121): MLay seed 对照 + 2层×detail 组合
  - 未验证 (本次):
    * **decoder 侧直接访问多尺度 cluster tokens** — 唯一未探索的结构轴。
      writeback 将多尺度 context 压缩成单通道 message 注入 inst_feats, decoder 只
      能看到这份有损和。若 0.501 平台源于 writeback 瓶颈 (多尺度信息在压缩中丢失),
      则给 decoder 直接 cross-attend cluster tokens 可绕过该瓶颈。
      这是 goal.json 已解锁的突破方向①, 但 QMOD 用 gate 实现失败;
      DCA 用结构注意力 (decoder query ↔ cluster tokens) 实现, 信息流完全不同。
  - 矛盾/疑问:
    * QMOD (gate 版 decoder query 调制) 失败 0.4930 — 但 gate 机制本就在 banned 家族,
      且其作用点是 writeback message, 不是给 decoder 新增注意力通道
    * 若 DCA 也 ≤0.501 → 排除"writeback 瓶颈"假设, decoder 无需直接 cluster 访问

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M123-DCA (Decoder Cluster Cross-Attention)**:
    * 验证假设: "0.501 平台源于 writeback 有损压缩; decoder 直接读多尺度 cluster tokens
      可绕过瓶颈, 提升定位精度"
    * 结构: 每个 Decoder_layer 新增 `qca` CrossAttentionLayer, decoder query 作为 Q,
      多尺度 cluster tokens (bank 聚合, [256,64,8]) 作为 KV → 直接提取场景级 context
    * 与 QMOD 区别: QMOD 是 query 注意力加权后 gate writeback message (gate 家族);
      DCA 是 decoder 新增独立注意力通道 (新计算图), 不触碰 writeback
    * 若 >0.501 → decoder 直连 cluster context 是破板方向, 与 encoder-side 机制正交可叠
    * 若 ≤0.501 → 排除 writeback 瓶颈假设, 资源回 M115-M119 批次
    * 非调参: 新计算图 (attention 通道), 无新超参, 复用 nhead=8/d_model=256

## 6. Next Batch
  → M123-DCA → 见 pipeline/designs/exp_design_20260821-052214.md
================================================================================
