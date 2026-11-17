# Motivation Review - cluster_project

## 1. Goal

最新用户主线是不同层级的注意力/信息交互真实更新inst_feats，再与query生成mask；监督仅为辅助。完整目标在本轮不可变goal_snapshot.json中，原20条约束与11项banned不变。
ScanRefer目标0.5100，历史M95为0.5020，baseline为0.4894，gap0.0080；本轮无新训练指标。

## 2. Story Status

| 假设/问题 | 状态 | 证据 | 缺口 |
|---|---|---|---|
| M95已有层间query注意力 | 源码不支持该命名 | CTF forward未读取query/child maps，实际分尺度FFN及HCG组合gather | 不是对整个模型语言/query作用的否定 |
| 层级消息真正进入mask特征 | 静态路径支持、原模块路径活动 | 12项AST断言；原模块token干预和梯度非零；Encoder写回及prediction_head依赖 | 完整原生特征干预/梯度仍未执行 |
| 无效padding可能影响有效点更新 | 构造CPU fixture支持路径风险 | 原有效特征delta0.09381044、固定query logits delta0.04313642；同形状logits重放/路径阻断delta0 | 实际训练特征和任务伤害未知 |
| 真实TRAIN输入有触发条件 | 固定小样本存在 | 4群组/4场景/16表达式；预注册配对667/2329与406/1441，输入两次精确重复 | 仅取样和源码推导的padding长度，不是网络特征捕获 |

## 3. Experiment Assessment

| 对象 | 已有结果 | 本轮定位 |
|---|---|---|
| baseline / M95 | 0.4894 / 0.5020 | 已有结构和指标对照，不当作新机制收益 |
| 四个旧监督候选 / M201 | 既有诊断、准入和中断记录保留 | 最新用户授权下仅为辅助，不因到期或空槽自动续做/恢复 |
| 新主线候选 | diagnosis转资源blocked，六门槛仍未通过 | 完成源码/CPU对照、原生输入与CPU权重准备；尚无新结构模型 |

## 4. Gap Analysis

- 已完成：源码与远端源码哈希匹配；M95固定权重fe5e4a5f...和配置a18f2c6f...核对；CPU模型严格装载847个参数tensor，两项序列化缓冲区等值核验。
- 原严格跨形状控制两次FAIL：1.1920928955078125e-6大于原1e-6。保留初始失败和局部对照修订；不提高阈值，也不把后续同形状控制通过解释成旧FAIL被修复。
- 同形状4项路径控制通过，仅支持构造CPU模块中的均值->level_gate->有效特征路径。纯masked mean/normalization修补不是获准的新核心机制，不得凭此入队。
- 互补性、层级冗余、真实mask伤害、泛化收益、新颖性和完整原生backward仍未知。未做文献新颖性声称。
- 16:24:50+08资源观测：server-4 GPU0 free11994MiB、NVML PID2634704占20016MiB、原训练flock仍held；另两诊断flock可得。util0不代表可用，不删锁、不reset、不驱逐。

## 5. Design Rationale

本轮只建立一个点云特征路径诊断候选，不派生监督变体，不改原生产代码、训练配置或固定协议。
无CUDA的可执行准备已经完成；下一项判别测试是用同一M95权重、固定TRAIN输入捕获真实cluster/message/mask_feats。
该测试需要实际释放的GPU及原锁；当前不满足原独占守卫，不能用本轮CPU准备或空队列代替资源准入。
本轮不存在新架构的调参气味通过或科学准入声称；所有既有banned保留。

## 6. Next Batch

不新增训练批次。原生捕获协议和已CPU装载核验的可执行适配器见本轮hier_feature_73d9... bundle。
在新前台租约下先重新核实GPU/原训练及诊断flock和冻结文件，再运行适配器的GPU捕获分支；明确报告实际分母与所有FAIL。
依据真实特征诊断再选择一个不触犯禁令的结构机制；不得把这次实现风险修补冒充层级注意力创新。
