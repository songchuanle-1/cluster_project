# Motivation Review - cluster_project

本轮 dbeca5d6；审计整理时间为 2026-10-18 上海时间。研究动机和控制先冻结于 diagnostic_prereg.md；本文在 CPU 测试后整理，不伪称事前写成。

## 1. Goal
- 完整目标的唯一事实源：pipeline/goal.json，SHA256 42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec；24 项约束、11 项禁止均不修改。
- 主线是不同尺度的交互实际更新用于 query-point mask 的点云 inst_feats；效率只是约束，不是唯一贡献。Phase1 不调参。
- 目标 .5100；历史最佳 M95 .5020；差距 .0080。M203 的早期 .4144061804 不是最终效果。

## 2. Story Status
| 假设 | 状态 | 证据 | 缺口 |
|---|---|---|---|
| Fine 交互能沿点云分支影响最终 mask | 前轮有路径活动证据，不等于邻域有效 | tick_0571f421/native_result.json，非本轮新增测试 | 自身传递与非自身信息没有分开 |
| Fine 邻域内容在保持自身项和非自身范数后仍影响 mask | 本轮 CPU 正确性通过，原生待测 | tick_dbeca5d6/cpu_contracts_result.json | 训练权重上的同前缀回放 |
| 层级差异化点云更新提高整体精度 | 未验证 | M203 正在训练；前三次 VAL .2966/.3788/.4144 | 终态原始 VAL、预定比较及不确定性 |

## 3. Experiment Assessment
| 实验 | mIoU | 与动机的关系 | 对故事线贡献 |
|---|---|---|---|
| 历史 M95 | .5020 | 主线参考 | 不是本轮新实验；诊断参考权重不等于已验证历史最佳权重 |
| M202-HDS | .4946560264 | 已训练的层级点云读出实现 | 未超过 M95，不重启或做第三次模型修订 |
| M203-FLE | 早期最佳 .4144061804 | Fine 接收者相关交互，中粗层保持原设计 | 尚在第 4/50 轮，不能判终态好坏 |

## 4. Gap Analysis
- 既往 normal/uniform 控制改变了自身权重与邻域贡献，不能单独证明有用的邻域内容。
- 本轮固定 U=S+R 中的 S，只在 fine leaf 内重排 R 并匹配每个接收者、每个头的范数；检验内容作用，不新增模型。
- 早期 TRAIN 小样本即使有差异也不是泛化改善、整体误差下界或论文创新成立。核心创新仍未确立。

## 5. Design Rationale
- 先做成本最低的算子对照：8 类 CPU 检查通过，CUDA 未初始化。
- 再做完全不占卡的准备：时间选定第 2 轮 last 快照，严格载入权重，固定 8 个 TRAIN 场景、32 条表达，8 个原生 CPU 整理批通过。
- 首次准备因部署 work_dir 路径适配被原始 SHA 拒绝；失败保留，随后结构化核对除该已授权路径外所有配置相同。模型九个文件未改。
- 入射 query 前缀、采样和几何固定。所谓 fixed-query 指固定候选 query 索引；下游最终 query 特征仍由原生 decoder 计算，不能解释为完全隔离 query 特征的因果实验。
- 两卡均被占用且 server4 三种独占锁都属于原训练，故原生回放待资源；这不是科学拒绝，也不是全部路线耗尽。

## 6. Next Batch
- 仅续做 stable ID fle-self-neighbor-content-separation，见 pipeline/designs/exp_design_20261018_dbeca5d6.md。
- 未增加训练队列、准入、新模型、loss/gate/routing/残差变体，也未动其他项目、调度或正在运行的权重。
