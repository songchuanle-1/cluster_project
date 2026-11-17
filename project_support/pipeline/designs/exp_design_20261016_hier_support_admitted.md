# Experiment Design - cluster_project

Status: DRAFT / CONDITIONAL; primary stable ID: m95-hierarchical-mask-feature-path-audit.
用户时间：2026-10-16，Asia/Shanghai。当前租约5df76ddd906e4741b57970488d4b33bd，不改其deadline。

## 1. Motivation

目标原文：面向ScanRefer三维语言定位，研究不同层级承担不同注意力/信息交互作用的轻量结构机制；真实更新点云/超点inst_feats，再与query特征共同生成mask；监督仅作辅助。完整目标副本及20约束/11禁令绑定原goal SHA，不改数据、seed1999、epochs50/max_iters70、损失、注入位置、scale256/64/8、d256或head8。
用户补充：显存优化只是参考，不是唯一方向。因此主问题为层级信息是否分工并改善点特征；效率作为Pareto约束，不能以降低显存替代效果或创新。

## 2. Current Best Results

| Experiment ID | Config | State | Best mIoU | Acc@50 | spmIOU | Epochs |
|---|---|---|---|---|---|---|
| model_base1 | 历史baseline | 历史结果 | 0.4894 | 本轮未核验 | 本轮未核验 | 本轮未核验 |
| M95-CTF-HCG-CSORT | 原冻结M95配置 | done_earlystop | 0.5020 | 本轮未核验 | 本轮未核验 | 22/50；冻结诊断checkpoint另为epoch16 |
| M39-C2C | 历史c2c配置 | done_earlystop | 0.4865 | 本轮未核验 | 本轮未核验 | 约19/50；不重开 |

新方案指标、GPU峰值、native backward与新颖性均未知。已有GPU占用不是M95自身的已测显存。

## 3. Analysis & Direction

### 3.1 主假设与具体缺口
HCG读回自己的细/中/粗祖先，点集覆盖嵌套；CTF并未增加层间注意力。这是静态计算图事实，但不能推出任务伤害。
条件假设H：若真实学习特征显示祖先证据重复且区分性不足，改为具有互斥空间支持的混合分辨率读回可提供更可区分的上下文。仅先测试该条件，不并行扩出多套训练变体。

### 3.2 变量和完整机制
每场景保留现有点/超点特征X[N,C]、三级精炼token T0/T1/T2，父映射p1:fine->middle、p2:middle->coarse。只用实际存在叶子及祖先，不把batch padding token视为几何节点。
对点i，f(i)、m(i)=p1[f(i)]、c(i)=p2[m(i)]。冻结三个支持集：
```text
S0(i) = {fine j: p1[j] == m(i)}
S1(i) = {middle j: p2[j] == c(i), j != m(i)}
S2(i) = {coarse j: j != c(i)}
```
三组token的叶子后代互不重叠，且并集为该场景全部有效叶子；这只是覆盖性质，不保证信息量相同或task收益。细层分辨同一区域内部细节；中层观察较大区域内的其他部分；粗层提供其他大区域的场景上下文。这些角色仍需数据检验，不能把语义对象等同几何簇。
先使用现有通道按8头切分，不增加大Q/K/V/O投影，不做语言query top-k选择。算子原型：
```text
a_l(i,j,h) = softmax over j in S_l(i) [ <X_i,h, T_l,j,h>/sqrt(C/8) ]
M_l(i) = concat_h sum_j a_l(i,j,h) * T_l,j,h
M_l(i) = 0 if S_l(i) is empty
```
候选整合时保留原M95的level_gate/out_proj/message_norm/原注入强度和残差写回，不新增gate或residual机制，不更改旧global_mean定义以混入padding修补。只替换readback消息的信息流，原CTF/CSORT及原loss保持。最终依赖仍为：
```text
M_l -> original scale fusion/projection -> inst_feats writeback -> original decoder -> mask = normalized_query @ mask_feats.T
```
本次原型只验证读回算子，不声称已经实现独立完整模型/config或完成原生整合。

### 3.3 梯度、退化与复杂度
值路径有alpha权重梯度，score路径还有softmax Jacobian；X既作为原特征也作为attention查询进入反向。固定映射本身不求导，符合现有partition边界。空支持集返回零且无softmax NaN；padding点输出严格零。单token集合退化为直接取值，多token零score退化为支持集均值。这些退化不等价于旧祖先HCG，不能用同一权重前后mIoU差当训练结论。
冻结三级token总数上限328；复杂度按E=sum_i,sum_l |S_l(i)|计，为O(E*C)，不会建立N*N关系。最坏支持集可能不均衡，不能把平均簇大小当最坏上界。
按叶子分组复用支持索引和K/V，按固定工作块分块查询；CPU正确性块大小5只是拆分不变性检查，不是模型超参。后续GPU块大小由工作内存预算确定而非验证集搜索。可在纯读回段使用非reentrant checkpoint，显式保存RNG语义，不包含有全局累加器副作用的整个CSORT forward。
“稀疏/分块”相对该算子的稠密参考可减小临时scores，不保证比已线性gather的M95更省显存或更快。全模型峰值、反向保留张量、稀疏backbone和decoder mask开销必须同口径测；不承诺30%/50%节省。

### 3.4 历史/原文区别与禁令检查
M39在每尺度token上做稠密自注意力、增加Q/K/V/O，再按祖先广播；本案点特征查询不同支持集token，不更新token间自注意力。TrueRoute将语言/decoder query选择的route注入特征；本案静态几何树切面不使用query top-k、attention pooling替换簇生成、路径选择或learned routing。原簇库、层数、scale、loss、batch size均不改。
Stratified Transformer原文摘要(2203.14508)已提出近密远疏key采样和变长显存实现；PTv2摘要(2210.05666v2)已有分组向量注意力/分区pooling。因此“层级/局部全局/省显存”不作为本项目独立创新。拟议差异仅限M95 token树上互斥覆盖的point readout和机制匹配对照，全面最近邻文献/既有attnpool族差异尚待补核；若实质落入banned家族则不准入，不改名规避。

## 4. Experiment Plan

| # | 同一候选内的测试 | 配置/样本 | 目的/否决条件 | 状态 |
|---|---|---|---|---|
| 1 | 集合覆盖/排除边/空节点 | 预注册构造树，不是TRAIN | 重叠、漏覆盖、padding进入支持集即FAIL | 本次执行 |
| 2 | 稠密masked参考 vs 分组SDPA | 同一构造输入、同一loss | float32前后向最大绝对差<=1e-6；float64额外独立1e-10，不能放宽或覆盖旧FAIL | 本次执行 |
| 3 | chunk/checkpoint等价 | 同一算子、seed1999、dropout0 | 各输入梯度及固定query输出超原阈值即FAIL | 本次执行 |
| 4 | 支持内/排除token干预、断路对照 | 同一次捕获、固定query | 纳入边必须能改变输出，排除边/阻断路径应零变化；只证明路径活动 | 本次执行 |
| 5 | 原生M95特征捕获与条件诊断 | 冻结TRAIN组0/60/101/124及原checkpoint | 重复/回放不通过则不解释机制；不得用VAL选样 | GPU未满足原守卫，未运行 |
| 6 | M95 / 相同支持但均匀权重 / 三层都用祖先 / 本案互斥支持 | 同一原生捕获，保持query/loss与通道预算 | 区分额外感受野、attention选择与覆盖分工；无重复证据则不得声称去冗余有效 | 未运行；不是四个训练队列项 |
| 7 | 一个核心结构的独立整合与native backward | 原seed/schedule/data/loss | 六门槛都通过后才允许提出一项训练准入 | 未实现/未准入 |
| 8 | 统一训练后比较及效率 | ScanRefer原VAL；bs1/warmup20/repeat100 | target0.51；FLOPs<=10G按原口径；显存+15%需>=+0.003mIoU；分支提升<0.002且平台停 | 尚未运行 |

场景为统计单位，固定总体mIoU及边界/同类干扰/关系表达子组；小样本诊断不足以定伤害阈值，冻结后不能挑子集/新seed。原native全模型正向/反向、一般化和效率未完成均记unknown，不当FAIL机制或PASS准入。

## 5. GPU Allocation Plan

| Server | GPU | Assignment | Config | Justification |
|---|---|---|---|---|
| server-4 | CPU | 本次构造算子正确性/梯度控制 | 隔离纯PyTorch程序，CUDA_VISIBLE_DEVICES为空 | GPU繁忙不阻止授权CPU准备 |
| server-4 | 0 | 原生捕获，仅原始守卫全部通过后 | 原M95冻结配置/权重 | 本次00:30:57+08余1551MiB，原训练锁占用；不可分配 |
| server-6 / 其他GPU | 未授权 | 不使用 | 无 | 保留现有白名单，不改调度 |

## 6. Implementation Checklist

- [x] 用户补充写入方案：显存是参考，任务特征分工为主。
- [x] 源码/历史M39路径有界核对；未重开失败候选。
- [x] 冻结支持集、公式、匹配对照、原阈值及数据边界。
- [x] 隔离原型及构造CPU前后向已执行：39项控制27通过/12项float32严格控制失败，失败不覆盖；以result.json为准。
- [x] 追加数值定位：相同形状重复/checkpoint开关的输出、梯度及query读出差均0；原M95训练权重读回的自身coarse路径与本案排除路径不同。calibration_result.json只作定位，不将原FAIL改PASS。
- [ ] 原生特征条件诊断与机制差异/文献进一步核对。
- [ ] 独立model/config及原生完整backward、统一资源测试、六门槛receipt。
- [ ] 只向实际需要的授权目标安全同步；本次不修改生产模型或队列。

## 7. Risk Assessment

支持集几何范围不等于对象语义；粗簇可能跨物体，排除父簇可能损失有益上下文。无额外投影可能限制表达力；不能靠随意加scalar/温度、改head/scale等调参补救。分组Python循环可能显著增加延迟；checkpoint只是时间换内存，不是新机制或免费收益。CPU构造控制不证明原生稳定性、显存收益、泛化或新颖性。原生及训练结果仍pending；不将本案直接入队，不删旧证据或放宽任何门槛。

执行后补记：原float32稠密/分组固定query读出差最高约6.20e-6，未通过冻结1e-6；float64独立控制通过、同形状checkpoint配对精确一致不能替代这一失败。double条件读出仍有约2.21e-6/4.22e-6差，说明读出误差不全来自最终float32矩阵乘；没有声称已找到/修复唯一原因。原型控制状态为inconclusive，不是训练准入或假设证伪。
CPU autograd引用的不同storage字节在本fixture稠密参考1553845、分组checkpoint1075940；这不是全模型峰值，不能推出GPU节省、相对M95优势或可在1551MiB空闲下启动。

## Post-Training Plan Frozen 2026-10-16

本节为首次训练准入前的追加冻结，不覆盖上文原始失败和当时未知状态。
稳定ID不变，当前物理独立实现为hds_canon_r1；数值修订1及纯前缀重计算修订2均已通过各自冻结控制。
4个TRAIN场景/16个表达的完整原生反向及24个点特征路径张量非零有限梯度已经验证，优化器步数仍为0。
这些仅证明机制可执行，不证明训练收益、普遍无伤害或独立新颖性。

用户明确表示“10G也可以的 超出也不多”。仅对当前十个已测源码/配置哈希接受原标准口径10.034588748G，
比原10G高0.34588748%；原始资源FAIL和两次修订历史保留，不授权第三次修订或其他实现超限。
M95同口径9.762532428G；推理中位延迟83.1302/83.6800ms，推理峰值均928491008字节，
匹配TRAIN峰值4293406720/4499342848字节（+4.7966%），不能外推到全部场景。

- 单项结构首筛M202-HDS：原ScanRefer TRAIN/VAL、seed1999、epochs50/max_iters70、batch2、loss与既有优化器不变，不使用测试集选机制，不新增seed、数据集或消融训练队列。
- 主要终点为原VAL总体mIoU；比较原baseline0.4894与M95 champion0.5020，正式目标仍0.5100。沿用既有验证频次、best选择和patience10。
- 预定义子组使用既有原始标注的unique/multiple及关系表达属性；边界子组仅按已有、预测无关的标注定义核验。缺少可复现标注定义或配对M95预测时报告未测，不事后挑有利子集。
- 按scene为聚类单位报告配对差与95%区间；独立scene不足或区间跨决策边界则为inconclusive。没有可用配对参考/独立重复时，噪声底未量化，不把固定常数当估计噪声。
- 预注册材料伤害判据：预定义、可配对且至少20个独立scene的子组，若相对M95的mIoU差的95%区间上界低于-0.003，标记material harm，不保留为有益主张。0.003是决策边际，不是已测噪声底；小样本单scene负例仅作诊断。
- 效率复核沿用bs1/warmup20/repeat100和相同标准FLOPs口径，报告中位/P90延迟及完整模型推理/TRAIN峰值；显存+15%需至少+0.003mIoU的原规则不变。本次只对冻结的10.034588748G实现有例外。
- 分支提升小于0.002且平台不升仍按原规则停止；不得通过调参、改阈值、验证集选实现或隐藏负子组结果制造收益。
- 首选已完成原生验证的server3物理GPU1，一张卡一个实验；server4物理GPU0保留授权但不重复启动本实验。当前卡占用和三项原始flock在实际启动时重新核验并由原生训练继承。
