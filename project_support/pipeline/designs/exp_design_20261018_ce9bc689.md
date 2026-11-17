# Experiment Design - cluster_project diagnostic continuation

## 1. Motivation
cluster: 面向 ScanRefer 三维语言定位，回归用户最初的点云特征更新主线，研究不同层级承担不同注意力/信息交互作用的轻量结构机制，目标 mIoU ≥ 0.51。核心路径是分层信息交互真实更新点云/超点 inst_feats，再与 query 特征共同生成 mask；不能把仅修改监督损失、沿用已有层级骨架或无效路由计算称为该主线创新。以多尺度 context-only 和 M95 为既有对照，先诊断层级互补性、局部细节及跨层信息是否真正进入 mask 特征，再依据证据选择一个可推导、可证伪的结构机制。监督与关系绑定仅作辅助诊断/匹配对照，不再取代主线。覆盖机制对照、泛化稳健性和同口径效率验证；已有收益不证明新的分层注意力有效，也不自动重开历史失败或禁止的路线。
本轮补齐因果对照的数值可重复性，不是训练变体设计。

## 2. Current Best Results
缓存M95=.5020,M203-FLE=.4885315597；本轮无训练/VAL/收益。

## 3. Analysis & Direction
见本轮analysis.md和analysis_summary.json；FLE行排列足以引起局部BN数值漂移，M95实际首层内核差异原因未知。

## 4. Experiment Plan
| ID | Purpose | Actual result | Next |
|---|---|---|---|
| native-train-prefix-repeatability-audit | 原始跟踪/坐标对齐/固定输入VJP/BN行排列/算法观测 | 11次原生反向、22次算子VJP含7次零控制 | M95实际原生描述与indice表绑定 |

## 5. GPU Allocation Plan
仅server4物理GPU0，本轮逐进程三锁；server3GPU1保留授权未使用；server4GPU1未授权。最终证据见final_environment.json。

## 6. Implementation Checklist
- [x] 冻结原checkpoint/input/seed/nativeflags；保存预注册与实际结果。
- [x] 原生前后向及有界固定输入控制；保持全部历史失败。
- [x] 复核生产源码/配置/权重哈希及GPU三锁释放。
- [ ] 未完成M95实际原生首层描述/indice绑定；同稳定ID续做。
训练模型、配置新建、commit/push、准入、队列、训练启动均未授权为本轮诊断的自动后续，实际未执行。

## 7. Risk Assessment
固定批次不证明总体效益、创新或全训练资源；观测可能影响时序；M95原因保持未知。不得把一次确定性配对当成普遍确定性，也不重试至匹配。

Status: diagnostic controls IMPLEMENTED;training NOT ADMITTED;scientific validation PARTIAL.
