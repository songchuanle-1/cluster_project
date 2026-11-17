================================================================================
  Motivation Review — cluster_project
  2026-08-20 18:13:13
================================================================================

## 1. Goal
  - goal.json:
    metric: mIoU ≥ 0.51 on ScanRefer
    description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
    cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'
    假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。"
  - Target: mIoU ≥ 0.5100
  - Champion: M95-CTF-HCG-CSORT = 0.5020 (seed1999 only; 已证 seed-敏感, true mean ~0.498)
  - Gap: +0.0080 (nominal) / +0.012 (vs true mechanism mean)
  - Phase: 1 NOT YET (check_goal 2026-08-20 18:07)
  - Active constraints: Phase 1 禁止调参, 只允许结构性机制变更
  - Active retentions: None (constraints[] 无"活跃保留"字样; 最近 10 条决策无
    route_change/question 含保留关键词 — 双源检查通过)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 有效 | confirmed | A1-A0=+0.0118 | 无需更多验证 |
  | Routing 有害 | confirmed | A3-A1=-0.0544 | 禁止 |
  | CTF+HCG 核心架构 | confirmed | M81=0.5012, M65=0.5002, M78=0.5008 | 基底确定 |
  | CSORT 跨尺度正交 | DISPROVED | 3/4 seed 负增益 (08-19 关闭) | 轴关闭 |
  | ORT / MEMBANK / SRL | disproved | M97=0.4920 / M110+M112 / M111+M113 | 轴关闭 |
  | **2层 legacy readback 达 champion 水平** | **NEW confirmed** | **M86=0.5010 (无解相关, 2层)** | **seed 稳健性待验证 (M120)** |
  | ctf_hcg 模式 2层 | disproved | M96=0.4940 (2层退化仅限 ctf_hcg 模式) | 轴关闭 (修正解释) |
  | 2层 × detail message 组合 | UNTESTED | det_mlay 包+config 已建, 从未运行 | **本次设计目标 (M121)** |
  | Cluster 对比 loss (CCL) | WAITING | M115 排队 | 等运行 |
  | Cluster 图注意力 (CGA) | WAITING | M116 排队 | 等运行 |
  | 双向 context flow (BCF) | WAITING | M117 排队 | 等运行 |
  | 跨模态 cluster 交互 (LCC) | WAITING | M118 排队 | 等运行 |
  | 自监督 mask 重建 (MFP) | WAITING | M119 排队 | 等运行 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95-CTF-HCG-CSORT | 0.5020 | CSORT 变体, seed1999 outlier | 名义 champion, 归因种子效应 |
  | M81-CTF-HCG | 0.5012 | 核心 CTF+HCG context 机制 | 确认核心架构 ✓ |
  | **M86-MLAY (2层 legacy)** | **0.5010** | **多尺度 readback 深度 2层, 无解相关** | **隔离出 context 深度为核心收益** |
  | M109-CSORT-MSG | 0.5010 | message 级 decorrelation | 与 M81 持平, CSORT 轴关闭 |
  | M96-CTF-HCG-2LAY | 0.4940 | ctf_hcg 模式 2层 | 退化仅限该模式, 轴修正 |
  | M110-MEMBANK / M112 | 0.4954/0.4890 | 跨 batch 记忆 | 失败, 轴关闭 |
  | M111-SRL / M113 | 0.4912/0.4510(run) | 空间重建辅助 loss | 失败, 轴关闭 |
  | M97-CHAMP-ORT | 0.4920 | champion 基底 ORT | 失败, 轴关闭 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context-only 有效 (+0.0118); CTF+HCG 1层 ~0.501; **2层 legacy (无解相关) 即达 0.5010**
  - 已排队 (M115-M119): CCL/CGA/BCF/LCC/MFP — 覆盖视觉侧+跨模态+自监督
  - 未验证 (本次设计):
    * **MLay seed 稳健性**: M86=0.5010 与 M95=0.5020 同级, 但 M95 已被证 seed-1999
      outlier (mean ~0.498)。MLay 是否同样 seed-敏感? 若 M120-s42 稳在 0.50+,
      MLay 是比 M95 更干净的 champion 基底。
    * **2层 × detail 组合**: detail message (D1=0.5003) 与 2层 readback (M86=0.5010)
      各自独立有效; 组合 (det_mlay) 是否叠加 → 唯一现成的"两条强机制叠加"测试
  - 矛盾/疑问:
    * M86 vs M96 对照: 同为 2层, legacy=0.5010 vs ctf_hcg=0.4940 → 解相关在 2层下有害,
      但在 1层下有益 (M81=0.5012)。模式×层数交互非单调, 进一步说明需独立验证 MLay 基底
    * 0.50→0.51 需 ~0.012 = 整个 context 收益量级 → 仍需新信息流路径 (已排队批次承担)

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M120-CTF-HCG-MLAY-S42** (seed 对照):
    * 验证假设: "2层 legacy readback 的 0.5010 是真实收益, 非 seed-1999 伪影"
    * 若 s42 ≥ ~0.500: MLay 成为新 champion 基底 (无 csort 依赖), 故事线更稳;
    * 若 s42 << 0.501: 与 M95 同样 seed-敏感, 2层基底需谨慎, 回归 ctf_hcg 1层
    * 非调参: seed 对照是 pipeline 2.3 多 seed 验证标准实践 (同 M112/M113/M114)
  - **M121-CTF-HCG-MLAY-DET** (2层 × detail message 组合):
    * 验证假设: "多尺度 readback 深度 (2层) 与 detail 消息粒度是互补信息流 →
      组合叠加可突破 0.5010 平台"
    * 组件独立有效: 2层=0.5010, detail=0.5003 → 若组合 ≥0.505, 直接逼近 0.51;
      若 ≈0.50, 说明两机制共享瓶颈, 排除组合方向
    * 结构性: message_type='detail' 是 dec.py 中已实现的独立消息构造分支
      (line 194 分支), 2层是 cluster_att_num_layers=2; 参数有据 (来自 D1/M86 实验)
  - 队列深度: waiting=5 < 可用卡5+1=6 → 需补; 补 M120+M121 → waiting=7;
    server-6 gpu7 空闲 (M86 已 kill) 且 server-6 队列无 waiting → 新实验入 server-6 队列,
    下 tick 自动推送利用 3 槽位

## 6. Next Batch
  → M120-CTF-HCG-MLAY-S42 (seed 对照) + M121-CTF-HCG-MLAY-DET (2层×detail 组合)
  → 见 pipeline/designs/exp_design_20260820-181313.md
================================================================================
