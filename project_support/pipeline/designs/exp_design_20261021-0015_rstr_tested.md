# 最终已测版本R2（更新于2026-10-20T16:15:59.990791+00:00）

以下原始设计保留历史DRAFT/未完成清单，最终当前状态以末尾§8–9及[已测bundle](<D:/project/cluster_project/pipeline/diagnostic_bundles/tick_99819673/tested_bundle.md>)为准。

# Experiment Design — cluster_project
Created 2026-10-20T15:58:56.636853+00:00; upstream `pipeline/reviews/motivation_review_20261020-2359_rstr.md`; stableID `hierarchy-reversible-sibling-token-transport`。

## 1. Motivation（为什么设计这批实验）
项目动机（原文）：cluster: 面向 ScanRefer 三维语言定位，回归用户最初的点云特征更新主线，研究不同层级承担不同注意力/信息交互作用的轻量结构机制，目标 mIoU ≥ 0.51。核心路径是分层信息交互真实更新点云/超点 inst_feats，再与 query 特征共同生成 mask；不能把仅修改监督损失、沿用已有层级骨架或无效路由计算称为该主线创新。以多尺度 context-only 和 M95 为既有对照，先诊断层级互补性、局部细节及跨层信息是否真正进入 mask 特征，再依据证据选择一个可推导、可证伪的结构机制。监督与关系绑定仅作辅助诊断/匹配对照，不再取代主线。覆盖机制对照、泛化稳健性和同口径效率验证；已有收益不证明新的分层注意力有效，也不自动重开历史失败或禁止的路线。

本轮用户明确继续设计试验。23:47Shanghai快照active0/target3，candidate_budget3，pending7/8；只准备本候选，不以空GPU增加假设。已验证的是新依赖可到达mask；收益未验证。

## 2. Current Best Results（基于什么数据做决策）
| Experiment ID | Config | State | Best mIoU | Acc@50 | spmIOU | Epochs |
|---|---|---|---|---|---|---|
| model_base1 | 原baseline | 历史记录 | .4894 | 本轮未核对 | 本轮未核对 | 本轮未核对 |
| M95 | ctf_hcg_csort | 历史最佳 | .5020 | 本轮未核对 | 本轮未核对 | 本轮未核对 |
| RSTR诊断 | 冻结M95epoch16 | 完成8TRAINscene/32expr | 未训练 | 不适用 | 不适用 | 0 |

## 3. Analysis & Direction（方向分析）
有效既有轴是context/CTF/HCG；显式routing与大型投影等原ban不变。缺口是direct sibling source dependence；不是已有祖先信息完全缺失。新算子前景7/8变差是风险，content优于strict mismatch6/8仅支持内容关联有作用。没有收益方向选择或超参修正。

令T_i∈R^256为最终CTF FFN后的细token，n_i=bincount(point-to-fine)_i计有效超点行；parent来自cluster_ids_list[1]，零mass/padding排除。用原8heads、d=32。各parent各head：
Q_ij=softmax_j(T_i·T_j/√d)；A_ij=min(π_iQ_ij,π_jQ_ji)，π_i=n_i/Σn；i≠j时P_ij=A_ij/π_i，P_ii=1−Σ_j≠iP_ij；T'_i=Σ_jP_ijT_j。

推导：offdiag P_ij=min(Q_ij,π_jQ_ji/π_i)，所以P_ii≥Q_ii≥0，P1=1。π_iP_ij=π_jP_ji，从而πᵀP=πᵀ，逐head Σn_iT'_i=Σn_iT_i。只替换fine bank；middle/coarse、CSORT rawbank loss、原fusion、query与mask suffix沿用。**不声称融合后或logit均值守恒**。

梯度：离散FPS/ids/n固定；T经value和Q两条可微路径进入P T，min等值处采用框架次梯度；无新增trainable tensor，原CTF FFN须从native loss收到有限非零梯度，另retain transport output/input梯度证明新边参与。单token/常量值为identity；高selfdot可能饱和须测mobility，本轮mean offdiag约.494，非no-op。跨parent新算子Jacobian应0（原祖先间接路径不在此断言范围）。

成本 O(CΣ_g k_g²)，attention内存O(HΣ_g k_g²)；原生每表达Σk²=1168–1494，不能假设均匀4叶。参数增加0，但有新非线性图和跨叶依赖，不是仅归一化/缩放或加小Linear。保留原8heads/seed1999/epochs50/max_iters70，无调参。M39/原文差异见upstream，整体新颖性未完成。

## 4. Experiment Plan（具体做什么）
| # | ID | Config Path | Purpose / Hypothesis | Expected Result | Priority | Depends On |
|---|---|---|---|---|---|---|
| 1 | RSTR | configs/Quard/ctf_hcg_csort_rstr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr.yaml | 同parent细叶内容传输 | 实际native路径与strict control可分；训练mIoU未知 | P0 | 全科学/资源/提交门槛 |

固定对照：无传输；全组fixed cycle affinity（π和值固定，accepted权重分布可能变化）；等n子集fixed cycle affinity（P_c=RPRᵀ，严格同权重多重集，报告可交换覆盖）。对照只诊断，不能按效果选一条训练变体。identity/逆置换/守恒阈值1e-6已冻结。native backward与full-source identity/row inverse/disabled-transport原parent一致比较都须报告，不能将冻结bank测试代替。

后续训练评估预注册：原ScanRefer训练/VAL split与每epoch原评估；test不用于选择。主mIoU与M95 .5020及baseline .4894对比，目标≥.5100；结构首筛seed1999，保持50/70。匹配无传输与固定错配机制对照需沿同训练设置评价，不额外seed搜索。按scene聚类配对区间；有效scene不足/区间跨决策界时标不确定。训练前无独立repeat噪声底，标未知。预定义子组为目标占多个fine叶、单fine叶、目标中层混合度、target/non-target；若子组相对M95下降≥.002且scene聚类95%区间上界<0，记material harm并不宣布稳健收益。小样本单场景不作自动否决。

## 5. GPU Allocation Plan（GPU 分配计划）
| Server | GPU | Assignment | Config | Justification |
|---|---|---|---|---|
| server-4 | 0 | 本轮native诊断/反向/同口径资源 | 本候选 | 严格knownhost+UUID+fresh idle+3flock，顺序单进程 |
| server-4 | 1 | 未分配 | 无 | 保留授权，不占空卡 |
| server-3 | 1 | 未分配 | 无 | 保留授权，不新增并行假设 |
训练后续只经准入receipt与原dispatcher，FIFO无指定卡号；server3GPU0/server6新dispatch禁用。

## 6. Implementation Checklist（实施清单）
- [x] 固定diagnosis、primitive与原生匹配对照，全部方向留档。
- [ ] 独立`model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr`包：复制原7源文件，新增sibling_transport.py，只修改CTF fine refined readback前的一处连接；配置数值与原M95完全一致。
- [ ] AST/无跨变体import/独立config；实际native loss backward与新路径gradient；完整source controls；同口径bs1/warmup20/repeat100 median/P90/峰值/FVCore≤10G。
- [ ] 已测bundle方可申请缺少的具体commit范围；目前不commit/push/production sync/入队/训练。授权不能由设计请求推定。
- [ ] 准入receipt/安全同步/原dispatcher/真实训练步增长，尚未执行。

## 7. Risk Assessment（风险评估）
平滑可能损伤目标细节；固定模型读出已见不利前景，是必须保留的风险。控制coverage部分、同8scene不随机、未量化总体噪声/optimizer峰值/整体新颖性；无泛化结论。新算子无参数不代表零计算；原FVCore可能漏不支持op，必须报告新增量和时延内存。资源阈值默认10G，memory+15%需训练+.003，不使用HDS特例。默认最多2个有证据预注册实现修订；失败按implementation/hypothesis/inconclusive区分，保留原R0与全部负面结果，不调精度/阈值/seed/FPS/温度。原M95源包完全保留。

Status: DRAFT / diagnostic implemented; independent bundle and remaining gates pending. No training admission.

## 8. Smell Check

参数增量0但并非无新图：同parent细叶之间新增值与内容关联路径；固定π可逆矩阵改变来源依赖，不是仅scaling/norm。原8heads/d32/seed1999/50/70不扫参。新增代码没有learned gate/大QKV/新残差模块，M39等历史whole-mechanism差异与public prior已说明。R1/R2只修实际源图数值顺序，不作为新实验或新贡献。三项结构/可解释固定值/因果假设要求满足；任务益处仍未训练验证。

## 9. 最终实现及剩余边界

独立8源文件+1配置、AST/hash、实际native backward、固定FPS membership下完整pooling+active encoder控制、最终R2的8scene匹配对照及同口径M95资源比较已完成。数值最大0，梯度642有限且传输输入/输出非零；严格对照与weightedmean仍低于原1e-6。R0/R1失败不可删除；R2为最后默认修订。

7/8场景前景较匹配无传输参考变差、6/8较严格错配更好；latency+25.28%，不称有效或轻量Pareto胜出。先前§4训练后评估/子组material-harm规则冻结不变；不额外seed/超参选择，不把tinycohort当训练收益。完整optimizer峰值/无cluster基线资源配置/噪声底/全局新颖性尚未知。

完整技术证据：`pipeline/diagnostic_bundles/tick_99819673/final_technical_review.json`。可审阅的提交范围：`pipeline/diagnostic_bundles/tick_99819673/tested_commit_bundle.json`。目前未commit/push/production部署/入队/训练，scientific_admission=false。下一步只在具体本地提交授权后继续原准入链，不要求重新授予已有GPU资源权限。
