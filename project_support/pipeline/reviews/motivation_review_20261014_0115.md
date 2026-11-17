# Motivation Review - Native Role Calibration

## 1. Goal
- ScanRefer mIoU target0.5100, M95 champion0.5020, baseline0.4894.
- The authoritative goal remains pipeline/goal.json: concrete localization
  error, independently structured lightweight mechanism and native controls.
  All18constraints/11bans, Phase1 no tuning and frozen schedule stay unchanged.
- No extra dataset, label collection, seeds, altered threshold or allocation.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| MAIN role weight overwritten | 原始来源事实保留；13案例原生校准已覆盖 | primary94与supplement70个MAIN/次级位点均吸引；组合方向13表达均同向 | 覆盖权重事实不是新结构或训练效果 |
| Normalized secondary mass changes supervision | 来源事实保留；原生梯度已解析 | 26primary/16supplement/562extension排斥位点均高于实际query-token阈值 | 不能把正常校准直接等同错误标签 |
| REL/OTHER overlap causes direct net repulsion | 该净排斥解释未出现；不否定全部语义机制 | primary43、extension8重叠位点均吸引；原缺失对照仍保留 | 未定义独立因果修复或新的参照物绑定结构 |

## 3. Experiment Assessment
| Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
|---|---|---|---|
| 五项固定checkpoint原生诊断 | 未产生新验证mIoU | 解析校准、原生GT读数及局部头响应 | 区分来源事实、梯度方向、当前错误与训练收益 |
| M95 champion | 历史0.5020 | 当前参照物定位基础 | 本轮未更新权重 |
| M200-TMR | 历史0.49527952075 | 已完成原生首筛，低于champion | 不重启、不调参或改名填槽 |

## 4. Gap Analysis
- 扩展清单在任何forward之前冻结：64新半质量场景、16无半质量比较场景，
  加原始桥接control4804，共81组320表达；不是80项独立匹配因果对照。
- 24排斥表达中2条当前support IoU失败；24条局部方向与指示器相反，
  22条与组合目标相反。头下降方向23/24指示器微增、22/24组合微增，
  最大组合变化1.6391277313232422e-6。没有优化器或训练收益。
- 完整语义方向与局部子集不是同一干预。原生float32微小响应、衍生误差、
  历史strict1e-6全forward失败、原始缺失disjoint对照必须保留。
- 不能要求训练前显著收益/固定伤害阈值；这里缺的是独立、可区分且满足
  Phase1约束的结构性干预，不是“必须先证明mIoU会提高”。

## 5. Design Rationale
- 本轮不建立独立model/config，不把优先级、分母归一化、删标签或PCGrad
  当作新核心。实际测试确有新信息，但没有证明其应变成训练候选。
- 三个稳定ID继续validation，不用缺乏新机制或未执行训练冒充科学反证。
- 资源并不阻塞：共享GPU7显存满足门槛，外部PID262355始终保留。
- 不能真实满足提前冷却要求：无外部资源阻塞，也没有两条独立已拒绝路线。
  不伪造no_information_gain、全局穷尽或截止时间；不为通过截止重复测试。
  收尾校验若拒绝此诚实的未闭环状态，保存其原始错误并abort释放租约。

## 6. Next Batch
- 复用已完成的校准/角色/头/原生任务事实，下一步先定义一个真正改变
  监督信息流的可证伪干预及匹配对照，并对照既有已关闭的监督单位、
  mask-aware matching、categorical ownership及梯度手术原语。
- 新核心未明确前，不重新测同一校准、不制造bare修补变体，也不入队。
- 确切证据及哈希见native_calibration_final_summary_20261014_0115.json；
  本评审不是postflight成功证明，也不建立有效冷却。
