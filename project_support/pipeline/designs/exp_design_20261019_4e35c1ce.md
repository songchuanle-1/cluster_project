# Experiment Design - cluster_project

## 1. Motivation
- 动机和约束绑定上游motivation_review_20261019_4e35c1ce.md及其goal SHA256；研究真实进入mask的层级点特征，不把空槽当证据。
- begin为design，快照2026-10-19 22:32:22上海，active1/target3、准入预算2、储备预算2。GPU1授权已生效，无须再确认。
- 先检验一个由原生源直接提出的错误假设，不为预算凑两项结构。预注册时间由prepare实际收据记录。

## 2. Current Best Results
| ID | 状态 | 最佳mIoU | Acc@50 | spmIoU | 进度 |
|---|---|---|---|---|---|
| model_base1 | 历史对照 | 0.4894 | 未知 | 未知 | 历史 |
| M95 | 历史最佳 | 0.5020 | 未知 | 未知 | 22/50 earlystop |
| M204-CPA | 监控登记运行 | 约0.4944 | 未知 | 未知 | 18/50；新增步数另核实 |

## 3. Analysis & Direction
- K0(B)=min(256,min_b N_b)来自PointCloudPartitioner.forward；固定场景细层支持可能依赖batch同伴。
- 若原生所有N_b>=256，此依赖在当前数据上不激活。代码反例不等于任务缺陷。
- sample_rdn在点数不超过2500000时保留所有点，np.unique仅重编号。只有这些场景原始超点数可判为实际支持数。
- 与padding/global_mean、feature-position moment、ancestry、表达移植及尺度边界诊断不同，不重开这些ID。

## 4. Experiment Plan
| ID | 配置 | 假设与测试 | 预注册判定 | 依赖 |
|---|---|---|---|---|
| hierarchy-native-batch-minimum-resolution | 原生M95，不建新配置 | 源AST配对控制；哈希绑定原生TRAIN全场景支持数 | 全覆盖、无未知且无支持小于256才否定当前数据前提；否则继续原生配对干预 | 固定源、配置、TRAIN注释及场景文件 |
- 按所有TRAIN scene_id字典序普查，不用mIoU、标签或旧结果挑场景。
- 缺文件、超抽样上限、读数异常单列未知。没有mask重放/backward时不记这些gate PASS。
- 如发现实际小支持，固定接收场景、checkpoint、query、目标，仅更换原生大/小同伴；先重验数值/资源/对照。

## 5. GPU Allocation Plan
| 服务器 | GPU | 本轮用途 | 限制 |
|---|---|---|---|
| server4 | 0 | 保留M204 | 不重启、不迁移、不改文件 |
| server4 | 1 | 已授权；本项普查不使用CUDA | GPU诊断仍需新鲜UUID、占用和三独占锁 |
| server3 | 1 | preflight不可达 | 资源/进程未知，不当作空闲 |
- 仅在钉扎server4原生环境CPU执行，线程数1；不读密码、不写训练数据、不复制大checkpoint。

## 6. Implementation Checklist
- [x] 诊断代码与生产模型分离，不改model/config或M204。
- [x] 预注册判据与源哈希；controller只在本轮租约/目标哈希一致时写项目。
- [ ] 实际全场景普查并核对缺失/未知分母。
- [ ] 按证据推进稳定ID，保留负证据和完整六段报告。
- 独立模型/config、backward、效率及训练后方案：没有可训练机制，不适用准入，不伪造PASS。

## 7. Risk Assessment
- 超采样上限一律未知。数据未变证明包括源/注释前后哈希、场景文件前后stat和内容哈希。
- 小支持只是入射证据，不证明mask改善；全覆盖零入射只否定当前数据特定前提，不否定分层注意力。
- 中断/时间不足不写成反证；不足保留pending测试并诚实收尾/abort。

## 8. Smell Check
- 无可训练变化、数值搜索、调权、norm/scalar/gate/routing变体；源反例仅验证检测，不选模型。
- 文献新颖性、总体效果、噪声底限未核实；不得称独立创新或完成科学准入。
