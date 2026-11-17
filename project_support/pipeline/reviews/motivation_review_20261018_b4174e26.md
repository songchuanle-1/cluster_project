# Motivation Review - cluster_project

2026-10-18 上海时间；CPU 对照事前记录于 tick_b4174e26/metric_prereg.md 及执行前补充，本文在结果后整理，不伪称事前写成。

## 1. Goal
- 完整目标唯一事实源 pipeline/goal.json，SHA256 42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec；24约束/11禁止不变。主线为不同层级交互真实更新参与query-point mask的点云inst_feats，效率不是唯一贡献。
- 历史M95 .5020，baseline .4894，目标 .5100，历史差距 .0080。Phase1不调参；本轮没有新训练机制。

## 2. Story Status
| 假设 | 状态 | 证据 | 缺口 |
|---|---|---|---|
| Fine信息路径参与mask | 以前有活动证据，不是任务收益 | tick_0571f421/native_result.json，缓存 | 训练终态及自身/邻域分离 |
| 固定成员下细层度量交互对等距变换稳定 | 本轮发现数值不连续反例 | lattice40旋转45度，输出最大差3.8265536 | 原生FPS组、真实训练特征与mask影响 |
| 此反例在真实场景必然出现 | 未证实 | 八TRAIN场景人工单叶56组合未复现 | 人工单叶不是原生fine成员 |
| 新分层机制提升任务精度 | 未验证 | M203第10/50轮，早期最佳 .4715447724 | 原始终态VAL及预注册比较 |

## 3. Experiment Assessment
| 对象 | 结果 | 与主线的关系 | 结论边界 |
|---|---|---|---|
| M203-FLE | 04:16:40确认原生步1200至1210增长 | fine接收者相关交互；中粗层保持原设计 | 继续原训练，未达到历史最佳 |
| 两个固定CPU夹具 | 16夹具-变换组合；14个等距/等比例组合中一个超1e-6；另2个非等距负对照 | 检验fine几何算子，不改模型 | 探针特征非训练inst_feats；无mask前向 |
| 独立反例确认 | 28精确整数cutoff并列；旋转后8个fallback翻转；NumPy误差约2e-15 | 定位严格浮点相等判定 | 整数并列oracle恢复仅是诊断，不是部署修复 |
| 八场景CPU准备 | 原生预处理32表达，56人工单叶组合无超限 | 准备真实几何并区分样本适用范围 | 没有原生CUDA FPS，不能宣称模型鲁棒性通过 |

## 4. Gap Analysis
- 以前的置换/并列测试没有覆盖坐标等距变换下cutoff判定；本轮补充的是不同可证伪性质，不是重复训练或改名变体。
- 40点整数格中旋转后最大距离残差约4.44e-16，严格相等条件却改变8点的leaf-mean回退；独立NumPy实现和整数距离oracle支持该实现层解释。
- 真正问题范围尚未知：真实原生fine组可能不含此类cutoff并列；训练特征、mask及mIoU伤害均未测。
- 原预注册泛称axis-aligned hierarchy不准确；实际是原生FPS/最近中心层级，已另留source_clarification.md，不改原注册或源代码。

## 5. Design Rationale
- 先登记稳定diagnosis，再用最便宜CPU对照实际测试；发现反例后继续独立核对和真实坐标压力测试，没有因一次失败就收尾。
- 原生FPS必须用CUDA，不能把CPU替代或人工单叶当作原生成员。已准备真实原始坐标/超点和GPU严格保护runner。
- 两张授权卡04:16:40均占用，现有训练与外部任务不动。所有本轮测试CUDA未初始化；GPU准备校验甚至未导入Torch。
- 不拟定随意epsilon、不扫参数、不改精度或原生1e-6门槛、不改变M203当前源绑定设计。它是实现数值风险，不足以宣布机制失败。

## 6. Next Batch
- 仅续做当前 fle-fixed-membership-metric-geometry-audit 的真实原生FPS/fine核核对，以及已有 fle-self-neighbor-content-separation 的mask机制诊断，资源空闲后按各冻结清单执行。
- 没有新model/YAML、准入、队列或启动；见 exp_design_20261018_b4174e26.md。科学收益和新颖性仍未知。
