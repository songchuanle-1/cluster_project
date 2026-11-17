================================================================================
  Motivation Review — cluster_project
  2026-07-31 22:03:01
================================================================================

## 1. Goal
  - Target: mIoU ≥ 0.5100
  - Champion: model_base1_quard2_c2f_enc_lite_posA_l1 (mIoU=0.5012, gap=+0.0088)
  - Description: "多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。routing 已被证伪，收益来自 context 而非 routing"

## 2. Story Status（故事线状态）
| 假设 | 状态 | 证据 | 缺口 |
|------|------|------|------|
| 多尺度 cluster context 提升特征表达 | confirmed | Lite+L1=0.5012 vs base=0.4894 (γ=+0.0118) | 天花板 0.5012 持续未破 |
| Token quality 是瓶颈 | partial | CTF=0.4995 (+0.0101), 接近但未突破 | CLN/WCA running 可进一步确认 |
| Readback/injection 机制有优化空间 | partial | SWI=0.4970 (有限), gate 系四连败 | 当前 gather 是最简方案，软分配未测试 |
| Cross-scale interaction 有价值 | testing | CSF waiting, XCA=0.4954 曾失败但机制不同 | 等待 CSF 结果 |
| Hard cluster assignment 限制信息流 | untested | 所有变体保持硬分配(gather one cluster per point) | **核心缺口 — 本批填补** |

## 3. Experiment Assessment（已有实验的动机视角评估）
| Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
|------------|------|-------------|-------------|
| Lite+L1 (champion) | 0.5012 | context injection 有效 | 确立 baseline ✓ |
| M41-CTF | 0.4995 | token FFN 精炼有效但未破天花板 | 证明 token quality 非单一瓶颈 ✓ |
| M40-SWI | 0.4970 | sigmoid injection 有限收益 | 证明融合权重优化不足 ✓ |
| M39-C2C | 0.4865 | within-scale cluster attn 有害 | 排除 intra-scale attention ✓ |
| M38-FLM | 0.4865 | gate/modulation 四连败 | 关闭方向 ✓ |
| M32-DRP | 0.5012 | routing 代码可删除 | 简化架构 ✓ |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context injection 有效 (γ=+0.0118), token quality 可提升但有上限, routing 无效
  - 未验证: **readback 机制的根本改进** — 当前 gather (硬分配) 是否限制了信息流？
  - 矛盾/疑问: 所有 token quality 改进 (CTF/CLN/WCA) 和融合改进 (SWI/gate系) 均无法突破 0.5012，暗示瓶颈可能在更基础的层面：**每个点只能获取单一 cluster token 的信息**
  - 关键洞察: 0.5012 天花板可能来自 hard cluster assignment——边界点、异常点、跨簇语义点被迫只用单一簇的上下文，而非从多个相关簇中软选择

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M45-NCR (Neighborhood Cluster Readback):
    - 填补缺口: "hard assignment 是否限制信息流"
    - 机制: top-K cluster attention 替代 hard gather — 每个点通过特征相似度关注 K 个最相关的 cluster token
    - 与已失败方向的区别: SWI 改的是 scale 间融合权重 (不改 gather), gate 系改的是 token 调制 (不改 gather), CTF 改的是 token 质量 (不改 gather)。NCR 是第一个改 readback 选簇机制的
    - 预期成功: γ>0 vs champion → 证明软分配有价值，可进一步探索 K 值/attention 机制变体
    - 预期失败: γ≤0 → 排除 readback 选择机制瓶颈，聚焦其他方向 (cross-scale 交互、iterative refinement)

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260731-220301.md
================================================================================
