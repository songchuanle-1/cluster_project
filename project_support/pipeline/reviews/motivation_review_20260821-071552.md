================================================================================
  Motivation Review — cluster_project
  2026-08-21 07:15:52
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
  - Phase: 1 NOT YET (check_goal 2026-08-21 07:07)
  - Active constraints: Phase 1 禁止调参; 突破方向①(cluster context 调制 decoder query)
    已解锁(用户 08-10); 禁 N² attention; 禁 gate系; FLOPs ≤ 10.0G
  - Active retentions: None (constraints[] 无"活跃保留"字样; 最近 10 条决策无
    route_change/question — 双源检查通过)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 有效 | confirmed | A1-A0=+0.0118 | 无需更多验证 |
  | Routing 有害 | confirmed | A3-A1=-0.0544 | 禁止 |
  | CTF+HCG 1层 ~0.501 | confirmed | M81=0.5012, M65=0.5002, M78=0.5008 | 基底确定 |
  | MLay (2层 legacy) 达 champion | confirmed (单 seed) | M86=0.5010 | M120/M122 seed 对照运行中 |
  | CSORT/ORT/MEMBANK/SRL | disproved | 多 seed 负增益 | 轴关闭 |
  | CCL/CGA/BCF/LCC/MFP 新机制批次 | WAITING | M115-M119 | 等运行结果 |
  | **decoder 直接访问 cluster tokens** | **UNTESTED** | 所有机制均 encoder-side | M123-DCA 已排队 |
  | **decoder 通过语言通路读 cluster (DCM)** | **UNTESTED** | 与 DCA 正交 | **本次设计** |

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
  - **关键观察**: ~0.501 平台横跨所有 encoder-side 机制。writeback 是
    `inst_feats + gate*message` 的单通道有损和, decoder 只看到有损后的 inst_feats,
    多尺度 cluster tokens 从未被 decoder 直接读取。M123-DCA 用"专用分支"给了 decoder
    直接访问, 但"共享语言通路"访问从未被测试。

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context-only 有效; CTF+HCG 1层 ~0.501; MLay 2层 legacy ~0.501
  - 已排队 (M115-M119): CCL/CGA/BCF/LCC/MFP — 全部 encoder-side
  - 已排队 (M123-DCA): decoder 专用分支 cross-attend cluster tokens (dedicated qca)
  - 已运行 (M120/M121): MLay seed 对照 + 2层×detail 组合
  - 未验证 (本次):
    * **decoder 通过语言通路直接读 cluster tokens (DCM)** — 若 writeback 有损和是
      瓶颈, 那么 *任何* decoder 侧 cluster 直接访问通道都应破 0.501 平台。
      DCA 测试"专用分支是否必要"; DCM 测试"共享语言通路是否足够/是否破坏语言接地"。
      两者共同覆盖 decoder 侧假设的完整证据空间:
        - DCA>0.501 且 DCM>0.501 → decoder 直连 cluster 破板, 通路实现无关
        - DCA>0.501 且 DCM≤0.501 → 专用分支必要, 共享通路稀释语言注意力
        - DCA≤0.501 且 DCM>0.501 → 共享通路(语言+cluster 联合注意力)才是关键
        - 两者都≤0.501 → 排除 writeback 瓶颈假设, 资源回 encoder-side
  - 矛盾/疑问: QMOD (gate 版 decoder query 调制) 失败 0.4930 — gate 家族, 作用点
    writeback message; DCM 不触碰 writeback, 不改 gate, 只扩展 qla 的 KV 记忆集

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M124-DCM (Decoder Cluster Memory)**:
    * 验证假设: "writeback 单通道有损和是 0.501 平台的瓶颈; decoder 无论通过专用分支
      (DCA) 还是共享语言通路 (DCM) 直接读到 cluster tokens 都能破板"
    * 结构: 复用现有 qla (query-language cross-attention), 把多尺度 cluster tokens
      (cat 后 [B, ΣK, C]) 沿 token 维 concat 到 lang_feats 上作为 qla 的 KV memory,
      掩码 = [lang_masks; cluster_pad]。decoder query 通过已有的语言注意力通路
      同时读语言和场景级 cluster context。
    * 与 DCA 区别: DCA 新增独立 qca 分支 (自己的 Q/K/V 投影 + LayerNorm);
      DCM 不新增模块, 复用 qla 的投影, 只扩展其 KV 集 — 信息流路径完全不同
      (共享通路 vs 专用分支)。
    * 若 >0.501 → decoder 侧 cluster 直连假设再添一证; 若 ≤0.501 → 判定
      "共享通路破坏语言接地" 或 "writeback 非瓶颈", 均推进故事线
    * 非调参: 新计算图 (qla 注意力分布扩展到 cluster tokens), 无新超参
      (复用 nhead=8/d_model=256), 无新模块

## 6. Next Batch
  → M124-DCM → 见 pipeline/designs/exp_design_20260821-071552.md
================================================================================
