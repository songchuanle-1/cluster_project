================================================================================
  Motivation Review — cluster_project
  2026-07-22 07:10:00
================================================================================

## 1. Goal
  - Target: mIoU ≥ 0.5100 | Champion: posA_l1 0.5012 | Gap: +0.0088
  - description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51"
  - Phase 1: NOT YET — continue exploring

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 提升定位精度 | confirmed | posA_l1 0.5012 vs base 0.4894 (γ=+0.0118) | 需要消融哪些尺度必要 |
  | context > routing | confirmed | A4-shuffle 0.4941, A3-true_route 0.4468 | 任何 routing 均有害 |
  | detail message 等价有效 | partial | D1-detail 0.5003 (仅差 champion 0.0009) | 需要干净复现确认 |
  | 3 尺度全需 | testing | M18-S2FM / M19-S2FC 在队列 | 等终态结果 |
  | cluster token 正交化有益 | testing | M17-ORT 刚启动 | 等终态 |
  | QSF gate 有效 | disproved | M6-QSF 0.4866 < baseline | 放弃 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  对每个已完成实验:
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | posA_l1 | 0.5012 | 3-scale context + L1 → 验证核心 context 假设 | champion, 核心证据 |
  | D1-detail (relaunch) | 0.5003 | detail message_type → 替代 context 聚合方式 | 近冠军, 第二有效机制 |
  | D1-detail (1st) | 0.4979 | 同上, 早停过早 | 收敛需 ≥18 ep |
  | A4-shuffle | 0.4941 | 随机路由对照 → 证实任何路由有害 | 排除 routing |
  | M1-QGC | 0.4939 | query-gated context → 简单 gate 无益 | 排除 query gate |
  | C1-layerscale | 0.4998 | LayerScale gate (stopped_unknown) | gate 提供近冠军但归入 banned |
  | M6-QSF | 0.4866 | query 进融合 gate → 有害 | 排除 QSF, 支持 M18/M19 方向 |
  | E4-res_detail | 0.4944 | residual+detail 无协同 | detail 独立有效, 不需 residual |
  | M16-CSR | 0.4875 (running) | cluster self-refine | 当前不看好 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 有效(+0.0118), routing 有害, detail 近冠军(0.5003)
  - 未验证: D1-detail 可复现性(stopped_unknown 非代码crash, 需干净复现)
  - 未验证: 哪些尺度对 context/detail 必要 → M18/M19 在队列
  - 矛盾/疑问: detail 0.5003 仅差 champion 0.0009, 是否统计噪声?

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M20-DET (D1-detail 复现):
    * 填补缺口: D1-detail 0.5003 是 closest-to-champion, 但 stopped_unknown
    * 假设: detail message_type 可稳定复现 ≥0.5000
    * 若复现成功: detail 成为 story 第二条可独立验证的有效机制
    * 若失败: 0.5003 是噪声, detail 不可靠 → 需要其他方向
    * 纯 config 复用, 无代码风险

## 6. Next Batch
  → 仅 M20-DET 一件, 用完最后一个 queue slot
  → 后续 M18/M19 终态后再设计下一批
================================================================================
