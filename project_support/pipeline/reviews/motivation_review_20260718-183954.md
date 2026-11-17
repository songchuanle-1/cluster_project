================================================================================
  Motivation Review — cluster_project
  2026-07-18 18:33:00
================================================================================

## 1. Goal
  - goal.json: 聚类路由机制 — 低分矩阵与点云特征高相关→cluster_attn更新点云特征→提升定位精度, target mIoU ≥ 0.51
  - Champion: posA_l1 0.5012 | Baseline: model_base1 0.4894 (γ=+0.0118) | Gap: -0.0088 | Phase 1 (check_goal 实测)
  - constraints[7] + banned[8] (goal.json 2026-07-18)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | cluster_attn 路由有效 | confirmed | posA_l1 0.5012 vs base 0.4894 (γ=+0.0118) | 距 target 0.0088 |
  | 路由不可或缺 | confirmed | noroute 0.4972 vs posA 0.5009 | — |
  | 收益来源归因(context/routing/residual) | in-flight | B5-residual(5/50)/C3-refine(队)/D1-detail(队) | 三机制变体结果待出 |
  | 位置编码影响路由 | in-flight | C2-posC 9/50 (Best=0.4722) 仍在上升 | 待收敛判定 |
  | 训练 schedule 释放收敛潜力 | blocked | constraints 禁单变体改 schedule | E1-cosine 16:43 撤回 |
  | 多 seed 稳定性 | deferred | 用户决策留 Phase 2 | — |
  | 聚类粒度敏感性 | untested | cluster_layer_nums 始终 [256,64,8] | 不同粒度如何影响路由质量？ |
  | 路由宽度敏感性 | untested | per_layer_topk_list 始终 [32,16,8] | TopK 宽度是否饱和？ |

## 3. Experiment Assessment（增量 — 自上次 review 20260718-161319）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | B5-residual | 0.4369 (ep5, running) | 残差注意力替代 context aggregation | 测试不同消息传递机制 |
  | C2-posC | 0.4722 (ep9, running) | 位置编码类型C消融 | 验证 pos encoding 选择 |
  | C3-refine | — (waiting) | MultiScale_Gather_Refine | 测试 refine 机制 |
  | D1-detail | — (waiting) | 独立点-簇归一化残差 | 测试 detail message type |
  | C1-layerscale | 0.4998 (终态) | gate 缩放 | gate 系三连败收官, 排除 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 机制轴已满仓 (B5/C3/D1 三变体全覆盖)
  - 位置编码轴在跑 (C2-posC)
  - **聚类超参数敏感性完全未触及**: cluster_layer_nums / per_layer_topk_list 固定为默认值, 不确定最优
  - 这些参数直接控制聚类粒度和路由宽度, 与动机「聚类矩阵与点云特征高相关」高度对齐
  - 若聚类粒度/路由宽度能 push ≥0.5020, 则证明聚类质量直接决定特征表达质量

## 5. Design Rationale（Q2+Q3: 为什么是聚类超参数调优）
  - **Q2: 填补什么缺口?**
    - 聚类粒度 (finer cluster): 更多初始 cluster 能否提供更精细的特征分组 → 提升 routing 精度
    - 路由宽度 (wider topk): 更多 context per cluster 能否提升 cluster token 质量
  - **Q3: 跑完后故事线推进到哪?**
    - 若 finer/wider > 0.5012: 聚类超参数是性能杠杆 → Phase 2 消融可加入超参数消融
    - 若 ≤ 0.5012: 默认超参数已充分 → 排除超参数轴, 聚焦机制改进
    - 两种结果都推进故事线 (消除不确定轴)
  - **零代码成本**: 复用 champion 模型包, 仅改 YAML 参数
  - **约束检查通过**:
    - FLOPs: finer 增加 cluster 数(256→512)仅增加 O(K*d) 向量量化, << 10G
    - 不改变 schedule/cluster_mode/gate_type/cluster_message_type
    - 不触犯 banned 列表任何条目
  - **与在跑/在队变体完全正交**: B5/C3/D1 改 cluster_mode, E2/E3 只改超参数

## 6. Next Batch
  → 见 pipeline/designs/exp_design_<ts>.md
  - E2-finer: cluster_layer_nums=[512,128,16] (更细聚类粒度)
  - E3-wider: per_layer_topk_list=[64,32,16] (更宽路由)
================================================================================
