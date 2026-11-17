================================================================================
  Motivation Review — cluster_project
  2026-08-20 19:28:09
================================================================================

## 1. Goal
  - goal.json:
    metric: mIoU ≥ 0.51 on ScanRefer
    description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
    cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'
    假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。"
  - Target: mIoU ≥ 0.5100
  - Champion: M95-CTF-HCG-CSORT = 0.5020 (seed1999 only; 已证 seed-敏感, true mean ~0.498)
  - Gap: +0.0080 (nominal) / ~+0.012 (vs true mechanism mean)
  - Phase: 1 NOT YET (check_goal 2026-08-20 19:07)
  - Active constraints: Phase 1 禁止调参, 只允许结构性机制变更; 队列深度下限 waiting ≥ 6
  - Active retentions: None (constraints[] 无"活跃保留"字样; 最近 10 条决策无
    route_change/question 含保留关键词 — 双源检查通过)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 有效 | confirmed | A1-A0=+0.0118 | 无需更多验证 |
  | Routing 有害 | confirmed | A3-A1=-0.0544 | 禁止 |
  | CTF+HCG 核心架构 | confirmed | M81=0.5012, M65=0.5002, M78=0.5008 | 基底确定 |
  | CSORT / ORT / MEMBANK / SRL | disproved | 多 seed 负增益 | 轴关闭 |
  | **2层 legacy readback 达 champion 水平** | **confirmed (单 seed)** | **M86=0.5010 (无解相关)** | **seed 稳健性待验证 (M120 s42, M122 s123)** |
  | 2层 × detail 组合 | UNTESTED | M121 running | 等结果 |
  | CCL/CGA/BCF/LCC/MFP (新机制批次) | WAITING | M115-M119 排队 | 等运行 |
  | **MLay seed=123** | **设计目标** | M86 s1999=0.5010, M120 s42 running | **补 seed 矩阵第 3 点** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95-CTF-HCG-CSORT | 0.5020 | CSORT 变体, seed1999 outlier | 名义 champion, 归因种子效应 |
  | M81-CTF-HCG | 0.5012 | 核心 CTF+HCG context 机制 | 确认核心架构 ✓ |
  | M86-MLAY (2层 legacy) | 0.5010 | 无解相关 2 层 readback | 隔离出 context 深度为核心收益 |
  | M109-CSORT-MSG | 0.5010 | message 级 decorrelation | 与 M81 持平, CSORT 轴关闭 |
  | M96-CTF-HCG-2LAY | 0.4940 | ctf_hcg 模式 2 层 | 退化仅限该模式 |
  | M110-MEMBANK / M111-SRL | 0.4954/0.4912 | 跨 batch 记忆 / 空间重建 loss | 失败, 轴关闭 |
  | M97-CHAMP-ORT | 0.4920 | champion 基底 ORT | 失败, 轴关闭 |
  | M85-QMOD / M88-QMOD-MLAY | 0.4930/0.4930 | 突破方向① decoder query 调制 | 失败, 无正交互 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context-only 有效 (+0.0118); CTF+HCG 1层 ~0.501; **MLay (2层 legacy) 单 seed 0.5010**
  - 已排队 (M115-M119): CCL/CGA/BCF/LCC/MFP — 视觉侧+跨模态+自监督, 已覆盖新机制批次
  - 已运行 (M120/M121): MLay s42 seed 对照 + 2层×detail 组合
  - 未验证 (本次设计):
    * **MLay 第 3 seed (s123)**: M86=s1999(0.5010), M120=s42(running)。若 M120/M122
      均稳在 ~0.50, MLay 成为比 M95-csort 更干净的 champion 基底 (无 seed-outlier 风险),
      后续所有新机制 (CCL/CGA/BCF/LCC/MFP) 都应优先在 MLay 基底上叠加。
      若 s123 掉到 <0.497 → 与 M95 同样 seed-敏感, 回归 ctf_hcg 1层基底。
  - 矛盾/疑问:
    * M86 vs M96 对照: 同为 2层, legacy=0.5010 vs ctf_hcg=0.4940 → 模式×层数交互非单调,
      需 MLay seed 矩阵确认 legacy 2层基底本身是否稳定
    * 0.50→0.51 需 ~0.012 = 整个 context 收益量级 → 新机制批次 (M115-M119) 承担,
      但需要一个稳健的 champion 基底作为叠加平台

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M122-MLAY-S123** (MLay seed=123 对照):
    * 验证假设: "MLay (2层 legacy) 的 0.5010 是稳健收益, 非 seed-1999 伪影"
    * 若 s123 ≥ ~0.500: MLay 三 seed (s1999/s42/s123) 均稳定 → 确立为 clean champion
      基底, 后续新机制叠加均以 MLay 为准 → 故事线更稳
    * 若 s123 << 0.500: MLay 与 M95 同样 seed-敏感 → 2层 legacy 基底不可靠, 回 ctf_hcg
      1层, 避免在新机制批次上叠加不稳基底
    * 非调参: seed 对照是 pipeline 2.3 多 seed 验证标准实践 (同 M120/M113/M114), 无新
      计算图, 纯验证性
  - 队列深度: waiting=5 < 容量5+1=6 → 需补 1 个; M122 入 server-6 队列 (当前 0 waiting,
    待 M120/M121 结束后自动推送, 利用槽位)

## 6. Next Batch
  → M122-MLAY-S123 (MLay seed=123 对照) → 见 pipeline/designs/exp_design_20260820-192809.md
================================================================================
