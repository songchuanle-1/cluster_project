================================================================================
  Motivation Review — cluster_project
  2026-08-01 11:15:00
================================================================================

## 1. Goal
  - Target: mIoU ≥ 0.5100
  - Champion: model_base1_quard2_c2f_enc_lite_posA_l1 (mIoU=0.5012)
  - Gap: +0.0088
  - Phase: 1 (NOT YET)
  - Motivation: "多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度"
  - Key finding: 收益来自 context 而非 routing (A3 routing=-0.0544)

## 2. Story Status（故事线状态）
| 假设 | 状态 | 证据 | 缺口 |
|------|------|------|------|
| 多尺度 cluster context 提升定位 | confirmed | A1 0.5012 vs A0 0.4894 (γ=+0.0118) | 需要突破 0.5012 天花板 |
| routing 路由有效 | falsified | A3=0.4468 (γ=-0.0544) | — |
| DRP (去掉路由死代码) 性能不变 | confirmed | M32-DRP=0.5012 (与 champion 持平) | — |
| 单通道 readback 是性能天花板 | hypothesis | 多个方向触碰 ~0.5012 但无法突破 | 需要验证替代 readback 机制 |
| Cluster token refinement 有效但有限 | partial | CTF=0.4995 (<0.5012) | 需要更强的 token→point 交互 |

## 3. Experiment Assessment（已有实验的动机视角评估）
| Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
|------------|------|-------------|-------------|
| posA_l1 (champion) | 0.5012 | 直接验证 cluster context 有效 | 确认核心假设 ✓ |
| M32-DRP | 0.5012 | 证明 routing 是装饰性代码 | 清理了因果链 ✓ |
| M41-CTF | 0.4995 | Cluster token FFN refinement | Token 质量提升有上限 |
| M17-ORT | 0.5005 | 正交正则化 near-champion | 正则化有帮助但不突破 |
| M26-ORT-HYB | 0.4998 | ORT+hybrid 组合 | 组合无额外增益 |
| M40-SWI | 0.4970 | Sliding window injection | Stop unknown, 未突破 |
| M33-DTW | 0.4968 | 动态时间规整 | 低于 champion |
| M22-XCA | 0.4954 | Cross-attention 融合 | 低于 champion |
| M34-Q2P | 0.4904 | Query→Point 直接读回 | 证实 cluster token 中介必要 |
| M42-WCA | 0.4890 | Weighted cluster aggregation | 证伪学习权重聚合 |
| M25-REF | 0.4892 | Refine mechanism | 证伪简单 refine |
| M39-C2C | 0.4865 | Cluster-to-cluster attention | 证伪 cluster 间 attention |
| M38-FLM | 0.4865 | Feature-level modulation? | 证伪 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: cluster context 有效 (γ=+0.0118)，routing 装饰性，DRP 等价
  - 未验证: 如何突破 0.5012 天花板？当前 readback 是瓶颈吗？
  - 矛盾/疑问: 多个方向触碰 ~0.5012 (ORT=0.5005, CTF=0.4995, ORT-HYB=0.4998) 但无法稳定突破。暗示 readback 机制本身是天花板——所有改进都在优化 token 质量，但 readback 的信息提取能力已达上限。
  - 瓶颈假设: 当前 additive readback (`feat += gate * message`) 对每个维度等权处理，无法利用 cluster context 选择性调制特征维度。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 唯一待补变体: M47-FILM — FiLM-conditioned cluster readback
  - 填补缺口: 测试 "readback 表达能力是天花板" 假设。如果 FiLM 能突破 0.5012，证明 additive readback 确实是瓶颈。
  - 因果机制: 当前 additive readback 只能"添加"信息，不能"调制"已有信息。FiLM 允许 cluster context 计算 per-dimension scale/shift 参数，选择性放大/抑制特征维度。例如：cluster context 发现某区域是"椅子"→放大与"椅子"相关的特征维度，抑制无关维度。
  - 预期: 如果 FiLM ≥ 0.5030，则 readback 天花板假设得证，后续可深化 FiLM 变体。如果 FiLM ≈ 0.5012，则天花板不在 readback 而在 token 质量，后续聚焦 token 改进。
  - 与 banned[] 的关系: FiLM ≠ scalar gate。FiLM 是 conditioning 机制（feature-wise modulation），有独立的 causal path: cluster→gamma/beta→modulate feats。banned 中的 gate 系 (cag/cfe/layerscale) 是 scalar gates on message flow。FiLM 改变的是 feature modulation paradigm，不是 message gating。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_<ts>.md (M47-FILM)
================================================================================
