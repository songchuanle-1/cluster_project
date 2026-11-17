================================================================================
  Motivation Review — cluster_project
  2026-08-01 01:03:01
================================================================================

## 1. Goal
  - pipeline/goal.json:
    Target: mIoU ≥ 0.5100
    Champion: model_base1_quard2_c2f_enc_lite_posA_l1 = 0.5012
    Gap: +0.0088
    Description: "多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。"
  - Phase: 1 (NOT YET)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 cluster context 提升定位精度 | confirmed | champion vs baseline: γ=+0.0118 | 消融各子机制的必要性 |
  | Routing 路由机制有效 | falsified | TrueRoute=0.4468 (-0.0544 vs champion) | 已证伪，DRP 确认 routing 为死代码 |
  | Cluster tokens 是必要中间表示 | confirmed | Q2P=0.4904 (≈baseline, 无 cluster→回归) | — |
  | Token 质量决定 readback 质量 | partial | CTF=0.4995 (FFN 精炼有效但未突破) | 单靠 token 质量不够，瓶颈在 readback |
  | 加权聚合优于均值池化 | testing | WCA running, 0.4714@ep9 (poor so far) | 待终态 |
  | 跨尺度融合提升 token 质量 | queued | CSF waiting | 待运行 |
  | Soft neighborhood readback 突破硬边界 | queued | NCR waiting | 待运行 |
  | **Readback 覆盖所有维度导致信息丢失** | **untested** | **无实验验证** | **本批 SHC 验证** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion posA_l1 | 0.5012 | 直接验证 cluster context 机制 | 确认核心假设 (+0.0118 vs baseline) |
  | DRP | 0.5012 | 去掉 routing 死代码 = champion | 证明 routing 无贡献，确立干净基线 |
  | CTF | 0.4995 | Per-scale FFN 精炼 cluster tokens | token 质量有效但天花板未破 |
  | SWI | 0.4970 | Sigmoid 加权注入多尺度融合 | 融合机制有效但未达 champion |
  | ORT-HYB | 0.4998 | 正交正则化 + hybrid context+detail | 组合机制接近天花板 |
  | Q2P | 0.4904 | 去掉 cluster tokens 直接注入 query | 负证据: cluster 必要 |
  | C2C | 0.4865 | Cluster-to-cluster self-attention | 方向失败 |
  | FLM | 0.4865 | FiLM modulation (gate系) | gate 方向已证伪 |
  | CMX | 0.4910 | Max pool aggregation | 不如 mean pool |
  | ORT (various) | 0.5005 | 正交正则化 | 有效但天花板未破 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: cluster context 有效 (+0.0118)，routing 无效 (DRP 确认)，cluster tokens 必要 (Q2P 确认)
  - 未验证: **瓶颈在 readback 机制的哪个维度？** 
    - Token quality (CTF tested → partial success, not the whole answer)
    - Aggregation quality (WCA testing, looks poor so far)
    - Cross-scale fusion (CSF queued)
    - Readback granularity (NCR queued, soft assignment)
    - **Readback dimensionality (SHC — UNTESTED): 当前 readback 覆盖所有 feature 维度，是否过度写入？**
  - 矛盾/疑问: 0.5012 天花板似乎很硬（CTF 0.4995, ORT 0.5005, ORT-HYB 0.4998 都无法突破），可能根因在 readback 的信息破坏性

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M46-SHC (Split-Head Cluster readback)**:
    - 填补缺口: 测试 "readback 覆盖所有维度 → 信息破坏 → 天花板" 假设
    - 机制: 将 point features 沿 channel 维度对半拆分，只更新一半 channels 用 cluster context，另一半保留 point-private 信息。通过 learned Linear 合并。
    - 预期: 如果天花板由维度全覆盖引起 → SHC 应 > 0.5012；如果持平 → readback 维度不是瓶颈
    - 故事推进: 无论是证实还是证伪都推进故事——证实 → 论文写 "我们发现 cluster readback 的全维度覆盖破坏了 point-private 信息，channel-split readback 解决此问题"；证伪 → 排除 readback 维度假说，聚焦其他瓶颈

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260801-010301.md
================================================================================
