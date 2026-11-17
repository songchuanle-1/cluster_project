================================================================================
  Motivation Review — cluster_project
  2026-07-28 08:03:01
================================================================================

## 1. Goal
  - pipeline/goal.json:
    Target: mIoU ≥ 0.5100
    Champion: model_base1_quard2_c2f_enc_lite_posA_l1 — 0.5012 (done_complete @ 36/50)
    Description: "cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度"
  - Gap: +0.0088 to target, +0.0118 vs baseline (0.4894)

## 2. Story Status（故事线状态）
| 假设 | 状态 | 证据 | 缺口 |
|------|------|------|------|
| 多尺度 cluster context 提升定位 | confirmed | champion 0.5012 vs base 0.4894 (γ=+0.0118) | 天花板 0.5012 如何突破? |
| ORT 正交正则提升 token 质量 | confirmed | M17-ORT 0.5005 (γ=+0.0111 vs base) | 最优 weight 待定 (M27/M28) |
| detail message_type 等价有效 | confirmed | D1-detail 0.5003 (γ=+0.0109) | 非超越, 持平 context |
| ORT + detail 组合协同 | disproved | M24-ORT-D 0.4955 (γ=-0.0050 vs ORT alone) | — |
| ORT + HYB 组合协同 | disproved | M26-ORT-HYB 0.4998 < ORT 0.5005 | — |
| ORT weight sweep (0.05/0.001) | pending | M27 (0.4946@ep19) / M28 (0.3853@ep3) 终态待分析 | 最优 weight? |
| 路由机制 (routing) 有独立收益 | disproved | A3-TrueRoute 0.4468 (γ=-0.0544), A4-shuffle 0.4941 | routing 信息有害 |
| refine/gather 迭代机制有效 | disproved | M16-CSR 0.4875, M25-REF 0.4892 | — |
| 正则化机制 (dropout/GELU) 未探索 | untested | dropout=0.0 everywhere, ReLU only | null |

## 3. Experiment Assessment（已有实验的动机视角评估）
| Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
|------------|------|-------------|-------------|
| champion (posA_l1) | 0.5012 | 直接验证 cluster context 有效 | 核心证据 ✓ |
| M17-ORT | 0.5005 | 验证 token 质量提升路径 | 第二条有效机制 ✓ |
| D1-detail | 0.5003 | 验证替代 message_type | 与 context 等价 ✓ |
| M26-ORT-HYB | 0.4998 | ORT partial rescues HYB | 组合无协同 ✗ |
| M24-ORT-D | 0.4955 | ORT+detail 组合 | 组合退化 ✗ |
| M22-XCA | 0.4954 | cross-scale attention | 不及 champion |
| M25-REF | 0.4892 | iterative refinement | 不及 baseline |
| M23-CMX | 0.4910 | max-pool aggregation | 不及 mean-pool |
| M21-HYB | 0.4898 | hybrid message_type | 组合抵消 |
| M1-QGC | 0.4939 | query-gated context | gate 机制增益有限 |
| M18/M19 scale | 0.4933/0.4944 | 2-scale ablation | 3-scale 确有必要 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: cluster context 有效 (+0.0118), ORT/detail 等价有效
  - 未验证: 
    (a) 正则化机制 — dropout=0.0 everywhere, 所有注意力/FFN 无 dropout, 训练收敛后快速过拟合 (peak ep13-25 后下降)
    (b) 激活函数 — FFN 只用 ReLU, GELU 在 transformer 中通常更好
    (c) 不同机制间是替代关系还是互补关系 — 三条路径 (context/ORT/detail) 各自独立 ~0.500x, 组合反降
    (d) ORT optimal weight — M27(w=0.05)/M28(w=0.001) running, 终态待分析
  - 矛盾/疑问: 为什么 context/ORT/detail 三者独立都达 ~0.500x 但无一超越? 天花板是数据限制还是架构限制?

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - Q1 缺口: 正则化完全未探索。所有实验都显示早停模式 (peak ep13-25 → decline) 强烈暗示过拟合。
  - Q2 填补方案:
    (a) M35-DOA: dropout=0.1 全局 — 首次引入 dropout 正则化, 对抗过拟合, 可能突破天花板
    (b) M36-GELU: activation_fn='gelu' — 首次使用 GELU 替代 ReLU, GELU 平滑梯度曲线改善优化
    (c) M37-CDL: Cluster Diversity Loss — 新 loss 强制 cluster tokens 互为正交, 类似 ORT 但以 loss 形式作用, 可与其他机制叠加
  - Q3 预期推进: 
    - 若 dropout > champion: 确认过拟合是主要瓶颈, 后续可扫 dropout 值 (Phase 2)
    - 若 GELU > champion: 激活函数是低成本增益
    - 若 CDL > champion: loss-based 正则比 feature-based (ORT) 更灵活可组合

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260728-080301.md
================================================================================
