================================================================================
  Motivation Review — cluster_project
  2026-07-18 16:13:19
================================================================================

## 1. Goal
  - goal.json: 聚类路由机制 — 低分矩阵与点云特征高相关→cluster_attn更新点云特征→提升定位精度, target mIoU ≥ 0.51
  - Champion: posA_l1 0.5012 | Baseline: model_base1 0.4894 (γ=+0.0118) | Gap: -0.0088 | Phase 1 (check_goal 实测)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | cluster_attn 路由有效 | confirmed | posA_l1 0.5012 vs base 0.4894 | 距 target 0.0088 |
  | 路由不可或缺 | confirmed | noroute 0.4972 vs posA 0.5009 | — |
  | 收益来源归因(context/routing/residual) | in-flight | B5-residual(1/50)/C3-refine(队)/D1-detail(队) 三机制变体 | roadmap §1.3 核心疑问 |
  | 位置编码影响路由 | partial | posA>posB(0.4953)>旧posC(0.4952,早停存疑) | C2-posC 重跑中 7/50 |
  | 训练 schedule 释放收敛潜力 | untested | champion PolyLR max_iters=70 仅训 50ep, 衰减视界溢出 | cosine/poly50/step 储备未跑 |
  | 多 seed 稳定性 | deferred | 用户 12:53 决策: 留到 Phase 2 | — |

## 3. Experiment Assessment（增量）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | C1-layerscale | 0.4998 (27/50 终态) | gate 缩放设计 | 排除 LayerScale; gate 系(cag/cfe/layerscale)三连败收官 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 机制归因三候选已全部在跑/在队 (B5/C3/D1), 机制轴无空位
  - 唯一未触碰的正交轴: **训练 schedule** — champion 的 PolyLR(70) 在 50ep 处仅衰减到中段,
    收敛尾部未压榨; roadmap §2.2 约束(不加语言路由/attnpool/qcond/prune)排除了其他储备 config
  - 队列缺口 1 (waiting=2 < 卡数+1=3)

## 5. Design Rationale（Q2+Q3: 为什么是 E1-cosine）
  - 唯一变量: PolyLR(70,p=4) → CosineAnnealingLR(T_max=50, eta_min=1e-6), 其余与 champion 完全一致
  - 若 >0.5012: 更优训练配方, 全部机制变体与 Phase 2 消融可继承 (乘法收益)
  - 若 ≤0.5012: 排除 schedule 轴, 确认 Poly70 已充分, 机制线为唯一杠杆 (排除亦是推进)
  - 零成本: config 已在本地+server-4 (2fa7bb87), 无新代码无需 sync
  - 与用户 12:53 "聚焦变体破指标" 一致; 用户已两次预告无异议
  - patience=15: cosine 中期 LR 偏高, best 可能后移, 防误杀

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260718-161319.md (E1-cosine, P1, 排 D1-detail 之后)
================================================================================
