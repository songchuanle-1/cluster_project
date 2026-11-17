# Motivation Review - cluster_project

## 1. Goal

本次为用户手动要求按研究思路设计；用户随后明确：显存只是参考点，不是唯一思路。主线仍为不同层级的注意力/信息交互更新参与mask生成的inst_feats。显存、延迟和FLOPs是共同约束，不以单纯省显存代替特征机制。
目标和全部约束以pipeline/goal.json为唯一主源，SHA256为6a11a897c8378c48934590d7603b5cbd18cac2d43da40690e0a7c72080f5478c；完整不可变副本由本次执行器保存到hier_support_5df76ddd906e4741b57970488d4b33bd/goal_snapshot.json。target0.5100，历史M95为0.5020，baseline0.4894；本次没有新训练结果。

## 2. Story Status

| 问题 | 已知 | 未知/边界 |
|---|---|---|
| 原M95如何更新特征 | 分尺度FFN，组合父映射，三个祖先token广播/融合；源码中的message写回inst_feats并参与mask | 祖先支持集重叠不等于重复信息有害，缺真实特征对照 |
| 各层是否有不同交互作用 | 现有读回按尺度取自己的祖先，不等于分工注意力 | 细/中/粗分工是新假设，不是诊断结论 |
| 是否只做显存优化 | 用户明确否定该单一定位 | 坚持任务特征机制与效率共同评价 |
| 原生诊断 | 输入/CPU严格权重装载已准备 | 当前原生GPU捕获仍未执行；构造样本不代表TRAIN |

## 3. Experiment Assessment

| 既有对象 | 已知指标/事实 | 本次定位 |
|---|---|---|
| model_base1 / M95 | 0.4894 / 0.5020 | 训练后统一对照，不能据此声称新机制有效 |
| M39-C2C | 0.4865；每尺度token之间稠密Q/K/V/O自注意力再广播 | 保留失败，不重开；本案研究point-to-bank读回支持集，不做token-to-token全局精炼 |
| TrueRoute | 0.4468 | 不采用query top-k路由/路由内容注入，不改其历史否决 |
| 四个监督候选/M201 | 原证据/门槛保留 | 范围暂停，不因本次设计恢复 |

## 4. Gap Analysis

实际错误分布、真实特征重复程度、边界伤害和关系子集收益都未建立。不能直接把“分层”或“注意力”作为创新结论。原生资源阻塞并不阻止本次明确支持集、推导、匹配对照和CPU算子正确性测试；但这些准备也不能代替原生诊断/训练准入。
本次只在原稳定ID m95-hierarchical-mask-feature-path-audit下准备一个条件式机制原型，不增加储备候选或队列。

## 5. Design Rationale

选择测试“同一查询点对应一个不重叠的混合分辨率树切面”：细尺度覆盖自身中簇，中尺度覆盖同粗簇的其他中簇，粗尺度覆盖其余粗簇。这给层级分工一个可验证的支持集定义，而不是单纯堆叠更多层/缩放/新loss。
与M39的算子和信息路径不同，但这种区别不自动构成新颖性。Stratified Transformer已有近密远疏的key采样；Point Transformer V2已有分组向量注意力和分区pooling。本案只提出在现有M95层级token库上的不重叠读回/支持集对照，完整文献新颖性仍未证实。
先通过集合覆盖、排除边、稠密参考与分组SDPA前后向等价、固定query路径、padding/空集合、chunk/checkpoint控制，再要求固定TRAIN学习特征及原生路径检验。CPU可行性不是准入。

## 6. Next Batch

见pipeline/designs/exp_design_20261016_hier_support.md。设计状态DRAFT/CONDITIONAL；无新训练批次。若真实诊断不支持重叠风险或支持集丢失有益信号，保留负结果，不靠调参/改样本补出收益。
