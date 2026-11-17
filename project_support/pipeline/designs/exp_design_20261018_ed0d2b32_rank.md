# Experiment Design - Conditioned Nonlocal Channel Diagnosis

## 1. Motivation
cluster: 面向 ScanRefer 三维语言定位，回归用户最初的点云特征更新主线，研究不同层级承担不同注意力/信息交互作用的轻量结构机制，目标 mIoU ≥ 0.51。核心路径是分层信息交互真实更新点云/超点 inst_feats，再与 query 特征共同生成 mask；不能把仅修改监督损失、沿用已有层级骨架或无效路由计算称为该主线创新。以多尺度 context-only 和 M95 为既有对照，先诊断层级互补性、局部细节及跨层信息是否真正进入 mask 特征，再依据证据选择一个可推导、可证伪的结构机制。监督与关系绑定仅作辅助诊断/匹配对照，不再取代主线。覆盖机制对照、泛化稳健性和同口径效率验证；已有收益不证明新的分层注意力有效，也不自动重开历史失败或禁止的路线。

## 2. Current Best Results
M95historical.5020,FLEcached.4885315597,target.5100. No newtrainedresult.

## 3. Analysis & Direction
将有限数值排查收束，回到原生层级点更新的跨区域通道。公式、控制和否定条件见nonlocal_rank_prereg.md。

## 4. Experiment Plan
| ID | Hypothesis | Matched control | Pending actual test |
|---|---|---|---|
| hierarchical-nonlocal-channel-rank-audit | 条件模块均值上下文Jacobian秩至多2 | owncoarse活跃/remote精确0,fullshape原生重建1e-6 | 1nativebackward,24tokenVJPs,48CPUJacobians |

## 5. GPU Allocation Plan
仅server4physicalGPU0，原生固定权重/数据/seed1999/batch2，活体检查与三锁；CPU双精度只作远端数学参照。

## 6. Implementation Checklist
- [x] 先审查再设计并预注册固定读出、完整源码和对照。
- [ ] 执行原生重建/VJP/CPUJacobian，保留全部失败和未知。
- [ ] 如需新结构，先做匹配任务干预和独立六门准入。
未新建训练model/config、未commit/deploy/queue/launch。

## 7. Risk Assessment
2scenes/8expressions不足以推断总体；秩至多2源于既有三尺度门控，不证明主线失败或新颖性。原始论文新颖性核对未进行，不宣称创新。外部encoder/decoder路径及参数可提供其他信息；低投影仅为风险，不是训练收益/伤害。

Status: DIAGNOSIS ONLY,NOT ADMITTED.
