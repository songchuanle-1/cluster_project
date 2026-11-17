# Motivation Review - cluster_project

## 1. Goal
- Goal source: pipeline/goal.json, unchanged 18 constraints and 11 bans.
- 项目动机：面向 ScanRefer 三维语言定位的具体错误，研究有核心新颖性、
  可推导且可证伪的轻量结构机制，目标 mIoU >= 0.51。先诊断候选覆盖、
  同类辨别和关系绑定、多尺度证据重复，再选择一个核心机制。
- Champion M95 0.5020; baseline 0.4894; gap 0.0080; Phase1 未达标。
- 本轮先恢复已退出宿主遗留的租约，不改变资源、调度或科学门槛。

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| 质量分支存在覆盖缺口 | observed | 新冻结采集：9/341 匹配候选被过滤 | 不等于共享模型缺失物理目标信息 |
| 被过滤候选没有任何原生目标误差路径 | disconfirmed realization | 固定低 IoU 原生 BCE/Dice 梯度非零 | 不能推出所有质量机制无效 |
| decoder 层间重匹配冲突 | disconfirmed realization | 83 表达、21 批次、6 次损失调用、两遍匹配一致 | 不否定其他 decoder 问题 |

## 3. Experiment Assessment
| Experiment | mIoU | Relation To Goal | Contribution |
|---|---|---|---|
| M95-CTF-HCG-CSORT | 0.5020 historical | 已有轻量结构参照 | 本轮未训练或更新 |
| quality/assignment capture | 未知 | 检查实际监督及匹配缺口 | 严格 1e-6 数值重复 PASS |
| native-path CPU control | 未知 | 区分分支过滤与目标信息缺失 | 8 项固定对照/源码检查 PASS，非新模型 backward |

## 4. Gap Analysis
- 31 个冻结 TRAIN 表达只来自 2 场景；52 个伴随表达保留，不代表全数据集。
- 质量过滤涉及 5 个表达，3 个最终被选候选处于过滤集；覆盖事实保留。
- 最终定位不直接读 quality scores，已有 mask 路径仍监督过滤候选。
- 删除 0.5 过滤阈值本身没有新的结构信息流，不能作为 Phase1 调参变体。
- 旧 decision-aligned ranking 拒绝记录不自动重开，旧 1e-6 FAIL 不被新 PASS 覆盖。

## 5. Design Rationale
- 两条独立可证伪实现分别检查目标误差信息路径与层间目标匹配。
- 不从单个总体 mIoU、梯度活动或小样本结果推断训练收益。
- 关闭的是泛化缺信息/阈值补丁和层间重匹配实现，不是所有研究方向。
- 更完整机制推导、原始文献新颖性和独立新模型均未完成，不作已完成声称。

## 6. Next Batch
- 本轮无准入；见 pipeline/designs/exp_design_20261009-0849.md。
- 新研究需独立且可部署的信息路径与预注册匹配干预，不复跑这两个等价探针。
