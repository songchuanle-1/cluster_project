# Experiment Design - cluster_project

此文记录诊断，不是一批新训练变体。控制事前定义见 pipeline/diagnostic_bundles/tick_dbeca5d6/diagnostic_prereg.md；本文在准备完成后整理。

## 1. Motivation
- 遵循 goal.json 原主线和全部冻结条件；区分点云 fine 注意力中的自身传递与非自身邻域内容。
- 快照 2026-10-18 00:12:02 上海时间，design，active1/target2/budget1。预算不是必须新增训练的指标；实际物理卡都占用。
- 角色：补机制证据缺口，而不是用小样本诊断代替训练效果。

## 2. Current Best Results
| Experiment ID | Config | State | Best mIoU | Acc@50 | spmIoU | Epochs |
|---|---|---|---|---|---|---|
| M95 | 历史参考 | 历史记录 | .5020 | 未知 | 未知 | 未知 |
| M202-HDS | 冻结 revision2 | earlystop | .4946560264 | 本轮未查 | 本轮未查 | 29/50 |
| M203-FLE | 已准入独立 FLE 包 | 00:49:42 确认训练增长 | .4144061804，早期 | 本轮未查 | 本轮未查 | 4/50，770/4686 |

## 3. Analysis & Direction
- 有效性仍未知。主线实现已接入点云到 mask 的路径，不据活动梯度、CPU 通过或早期上升声称主线已证实。
- HDS 的该实现未达到历史最佳；保持负证据，不重启、补第三修订或偷改其精确源绑定的 10.034588748G 例外。
- 本轮不重复前轮资料搜索，不主张新颖性。原有论文证据和差异仍受其已记录限制。
- 选择自项/邻项分解，因为它直接排除既往控制中自身贡献变化的混杂，无需新参数或调参。

## 4. Experiment Plan
| # | ID | Config Path | Purpose / Hypothesis | Expected Result | Priority | Depends On |
|---|---|---|---|---|---|---|
| 1 | fle-self-neighbor-content-separation | frozen native_manifest.json；不新建 YAML | 固定自身项和邻域范数，检验邻域空间内容是否影响原生 mask | 结果未知；无事前正效应量门槛 | P0 诊断 | 空闲授权卡及新鲜前台执行租约 |

- 时间选定的 last.pth 快照来自 epoch2，不按 best 分数挑选；原文件训练继续正常更新，快照绝不用于续训。
- 8 个固定 TRAIN 场景、各第一原生四表达组，按 SHA256 场景排序盲选。控制原生增强并记录每次实际输入指纹，不声称 CPU 准备和未来原生输入指纹必相等。
- 共同捕获原生前缀；normal/repeat/identity/source/suffix 容差仍 1e-6。改变 R 时 S 不变，逐头非自身范数匹配；坐标并列采用预注册的对称回退，若实际不改变内容记无信息而不造差异。
- 读出自身概率、非自身内容变化及最终 mask；固定候选 query 索引和各自选择的点级 IoU/BCE 为次要诊断。最终 query 特征由原生后缀重算，不声称完全隔离它。
- 不确定性按场景汇总与 bootstrap，仅 8 个 TRAIN 场景、早期权重，不外推泛化、创新或终态提升。

## 5. GPU Allocation Plan
| Server | GPU | Assignment | Config | Justification |
|---|---|---|---|---|
| server-4 | 0 | M203 原训练继续，不共享 | 原已准入配置 | 00:49:42 仍占用；三种锁由训练持有 |
| server-3 | 1 | 外部任务继续，不处置 | 不适用 | 00:49:42 占用已核实 |
| server-4 | 0 | 将来空闲后独占短诊断 | 本轮冻结 manifest | 当前资产和运行时验证完成；执行时必须再核实空闲和取得三锁 |

server3 的 GPU1 授权保留，但使用前须在该目标核对环境和数据/权重/代码指纹，不能将 server4 指纹直接当作 server3 已验证。

## 6. Implementation Checklist
- [x] 稳定 ID 事前登记；控制、checkpoint/场景选取事前冻结。
- [x] 8 类 CPU 算子检查通过；包括恒等、重构、范数、置换、并列、零、填充和梯度。
- [x] 9 源文件与部署配置/数据标注/数据源/checkpoint 的指纹冻结。
- [x] 权重严格 CPU 载入；8 个原生 TRAIN CPU 整理批、32 表达通过；未初始化 CUDA。
- [x] 原生 runner 准备、语法检查、manifest 验证通过；忙卡保护实际拒绝，未获取锁且未导入 Torch。
- [ ] 原生同前缀 mask 回放与场景不确定性；等待空闲卡，不能记通过。
- [ ] 终态 efficacy 按 M203 原冻结计划进行；不由本诊断替代。
- 不适用：新模型、新 YAML、git 部署训练、准入、排队或启动。它们本轮均未发生。

## 7. Risk Assessment
- 实现风险：原生 suffix 和 GPU 浮点对照尚未执行；CPU 和静态检查不证明所有 GPU 路径正确，失败须保留且不放宽容差。
- 科学风险：同范数重排仍可能分布外；早期、自选之外固定 TRAIN 小样本不是任务收益；并列回退可能少信息。正负差异均应如实报告。
- 资源风险：两张卡均忙；不得共享、驱逐、reset 或删他人锁。runner 需要当轮新鲜租约，未提供就不能执行。
- 时间界限：本轮原 deadline 2026-10-18 01:12:02 上海时间不改。实质非 GPU 工作完成后，以真实资源阻塞收尾，不等待截止或凑变体。

Status: PREPARED_NATIVE_PENDING_RESOURCE；非模型准入或科学 PASS。
