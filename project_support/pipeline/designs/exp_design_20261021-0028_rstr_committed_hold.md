# Experiment Design — RSTR 当前已提交、数值待解版本
更新于 2026-10-20T16:29:19.740458+00:00；稳定ID `hierarchy-reversible-sibling-token-transport`；commit `36b59daae6cdad2560024379eb5ed6acbcb20db2`。

## 1. Motivation（为什么设计这批实验）
主线是层级交互真实更新inst_feats并参与query-mask生成；目标mIoU≥.5100，M95历史最佳.5020，差.0080。完整冻结goal见上游 `pipeline/reviews/motivation_review_20261020-2359_rstr.md`。本轮只设计一个新结构，默认8/8pending上限及全部25约束/11bans未变。

## 2. Current Best Results（基于什么数据做决策）
| 记录 | 结果 | 范围 |
|---|---|---|
| baseline / M95 | .4894 / .5020 | 历史训练结果；本轮无新mIoU |
| RSTR committed R2 | 未训练，scientific_admission=false | 8TRAINscene/32expr，same cohort重复诊断 |
| 最终源图控制 / backward | 最大0；642梯度有限，传输入/输出非零 | 完整实际pooling+active encoder，固定FPS membership；不是上游backbone/FPS重编号等变 |
| 融合前加权均值控制 | **1/32表达1.027033878e-6 >1e-6 FAIL** | 早先9.5367e-7通过仍保留，不能挑通过复测 |

## 3. Analysis & Direction（方向分析）
原CTF是per-token refinement后按ID读回；祖先mean仍含间接信息，新假设仅针对细叶之间缺少直接内容和值交换。目标常跨细叶，新的路径和内容对应确实改变mask；相对同R2排序/CSR的无传输参考，FG7/8scene变差，相对严格错配6/8更好。平滑是风险，不是收益证明。M39全尺度投影attention+residual/LN、PCE物理接触点图、FLE同叶点图、CPA point-to-coarse和HDS支持集的历史状态不重开。MH/Sinkformers是公开既有primitive，整体新颖性未知。

## 4. Experiment Plan（具体做什么）
同一中层parent内，T_i为CTF细token，n_i为有效超点行成员数，π_i=n_i/Σn；沿原8heads/d32。Q_ij=softmax_j(T_i·T_j/√32)，i≠j时P_ij=min(Q_ij,π_jQ_ji/π_i)，P_ii=1−Σ_j≠iP_ij，T'=PT。只替换fine bank，保留原中粗信息和所有已有模块。数学上πᵀP=πᵀ，浮点实测必须满足原1e-6；不声称融合/投影/LN/logit均值守恒。

匹配对照固定：无传输；任意fixed cycle affinity（π和值固定）；等n子集fixed cycle affinity，保持P_c=RPRᵀ。所有GT只读出，query由无传输native固定，生产及每个对照都恰好传输一次。不同坐标顺序同步排列features/mask/pos/ids[0]并逆恢复，GT不移位。

当前动作是**数值hold**，无可自动执行的第三修订。后续如合法恢复，仍须同一ID/原门槛/原失败证据，不能换名重开或改FP32/seed/FPS/温度过关。训练后评估计划保留早先设计§4：原ScanRefer split/seed1999/50epochs/max_iters70，主mIoU与M95/baseline对比，scene聚类配对不确定性、预定义多叶/单叶/混合父簇及FG/non-target子组，下降≥.002且95%区间上界<0记material harm；test不选机制，不额外seed扫参。

## 5. GPU Allocation Plan（GPU 分配计划）
本轮仅server4GPU0做原生诊断，末次00:27Shanghai已核验无compute context、三类flock可用；没有新训练。server4GPU0/1及server3GPU1权限保持，不能把授权名单当实时空闲。没有GPU忙的停止理由；所有研究ID当前被scope/numeric门阻挡且pending8/8。

## 6. Implementation Checklist（实施清单）
- 已完成：独立8源文件+1配置、AST/import/hash、原生loss反向、完整源图控制、最终提交字节复测、同口径资源、全部负面留档。
- 已获人类明确授权并完成：只涉及这9文件的本地commit `36b59daa`；Git LF规整与旧AST等价，精确commit源重新测过。未把行尾当数值失败原因。
- 当前FAIL：融合前真实超点质量均值误差1.027e-6>原1e-6；没有准入receipt、推送、生产同步、入队、optimizer或训练。
- R1 failed、早先R2测试passed记录保持不可变；追加committed复测FAIL决定当前不准入。默认两次实现修订用完。
- 新误差分解：fresh capture2048groups/32calls，最差9.5367e-7，其中同坐标P32平稳性应用约−1.2614e-7、FP32乘法约−8.2754e-7，重构差0；不是原失败输入。只归档group最大值/最大坐标，未保留全channel误差/P/Tprime；不能说精确归因原FAIL或解除hold。

## 7. Risk Assessment（风险评估）
最终已提交字节同口径bs1,warmup20,repeat100：M95median34.515ms、P9037.217ms；RSTRmedian42.892ms、P9046.093ms，median+24.27%。计数9.762532428→9.763134540G，参数增量0，推理峰值各936763392bytes。FVCore不支持项仍列原结果；完整optimizer峰值/无cluster baseline资源差/总体噪声底/训练效果/整体新颖性未知。不宣称Pareto胜出。

按质量可逆凸组合，weighted variance预计收缩，本轮native约26.73%；可能损伤目标细节，FG负面结果不可用背景均值掩盖。canonical实现要求valid行连续前缀、无重合有效xyz；未覆盖不能补造。

## 8. Smell Check
零新增参数但新增直接跨细叶依赖和非平凡信息聚合，不是纯归一化/scaling小层；原8heads/d32不扫值。没有新learned gate、residual支路、大QKV、语言/query路由、point N²或重复层注入。R1/R2只修数值顺序，不冒充新机制。理论与技术路径成立不代替浮点门或效益。

当前状态：设计及本地提交完成；实现数值hold；核心假设未被科学证伪，训练收益未知。最新证据 `pipeline/diagnostic_bundles/tick_99819673/committed_gate_review.json`。
