# Research Pipeline Report - cluster_project
快照时间：2026-10-13T17:15:10.525220+00:00；生成报告时快照年龄：2223 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-14 01:15:09
================================================================================
  Target: cluster: 面向 ScanRefer 三维语言定位的具体错误，研究有核心新颖性、可推导且可证伪的轻量结构机制，目标 mIoU ≥ 0.51。多尺度 cluster context 是已有研究基础，不再把变更 pooling、selector、回写位置或变体数量当作研究主线。先诊断候选覆盖与边界、同类目标辨别与关系绑定、多尺度证据重复等问题，再依据证据选择一个核心机制；覆盖机制对照、泛化稳健性和效率验证。共享参照物一致性仅为待验证候选，不预设为最终方向。既有 context/routing 结果是历史证据，不等于新机制已获验证。

## Phase 1: Metric Target
  Target: mIoU ≥ 0.5100
  [✗] Champion: M95-CTF-HCG-CSORT — mIoU=0.5020 (gap to target: +0.0080)
       Epochs: 22/50, State: done_earlystop
  Phase 1: NOT YET — continue exploring ✗

## Baseline
  Baseline: model_base1 — mIoU=0.4894
  Champion vs Baseline: γ = +0.0126

## Phase 2: Story Verification
  (等待 Phase 1 达标后启动)

## Overall
  Phase 1: champion=0.5020, target=0.5100, gap=+0.0080
================================================================================
```

## 1. GPU Overview
- 仅列授权卡；未采集利用率、显存或进程时标为未知，不推断空闲。
| Server | GPU | Util | Memory | Process |
|---|---|---|---|---|
| server-6 | 7 | 未知 | 未知 | 未知 |
- 可用 GPU：未做实时占用确认，不能据此分配。
- 监控摘要（begin 已执行，不再重复探测）：
```text
================================================== 2026-10-14 01:15 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.194) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-6 (100.64.3.28) ---
  无训练进程

--- 队列: cluster_project ---
  server-4: done_earlystop=24 withdrawn=6
  server-6: done_earlystop=4
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| 无 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 快照内无运行任务 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 0（运行 0 / 认领 0 / 等待 0）；目标 2；准入预算 2。

## 4. This Tick's Actions
- 实际执行5项原生共享GPU诊断，218次完成组读数，去重110组/433表达/106场景；保留1次适配器失败，仅修正重复GT掩码断言，不改匹配、样本、分母或容差。没有新模型、优化器步、准入或训练启动。
- 原始25组97表达的校准/角色/任务/固定头读数已完成；补齐其余5个MAIN案例加桥接对照6组24表达。13/13来源案例的164 MAIN/次级位点均吸引；primary43+extension8 REL/OTHER位点均吸引。来源权重覆盖、质量差异事实保留。
- 新清单预测前冻结64半质量和16无半质量新场景，加桥接control4804，共81组320表达。mapper34647次读取用于此清单，不是重复独立population证据。比较场景不是匹配因果对照。
- primary26/supplement16/extension562排斥位点均高于原生校准阈值，解析梯度最大误差2.711e-8；不等同错误标签。扩展24排斥表达仅2条当前support IoU失败。
- 扩展固定头epsilon.001：24局部排斥方向中23指示器微增、22组合微增，最大组合变化1.639e-6；选中query/IoU无变化。严格全forward失败、缺失disjoint对照和float32衍生误差保留，不声称材料级伤害、全网络/训练收益或严格导数PASS。
- 01:49:26+08本地核验对应远端17:52:52Z，两端时钟差分别保留。GPU7空余80137MiB、利用率0%、外部PID262355/python928MiB仍在，两项目锁均可再获取。allocator峰值4111.55MiB/reserved4416MiB不是独占效率或进程峰值。
- 科学状态3个稳定ID仍validation，六项准入未通过，新核心未定义。执行状态以finish/abort及释放核验为准，真实截止02:15:10+08未修改。收据未生成，用量窗口/数值未知；收尾后仅在任务内补充，不重复加缓存、不当账单。

## 5. Decisions Made
- 不将简单优先级、分母归一化、删标签或PCGrad入队，不凑model/config或放宽准入；也不要求训练前固定mIoU收益/伤害阈值。
- 保留3条来源假设及未完独立机制验证。下一步复用事实，定义改变监督信息流、可证伪并与已关闭原语区分的机制和对照；不重复相同校准/头测试充当进展。
- 无真实资源阻塞、无两条独立已拒绝路线支持有效提前冷却；不伪造no_information_gain、全局穷尽、阻塞或截止，不为等截止重复测量。若校验拒绝此诚实未闭环状态，保留原始错误、abort核实释放，报告INCOMPLETE而非完成。
- 不操作其他项目、服务器/GPU、后台或自动化；Windows Pipeline-cluster_project保持Disabled。下次具体计划本轮未读取，未知。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
