# Research Pipeline Report - cluster_project
快照时间：2026-10-20T13:12:11.557636+00:00；生成报告时快照年龄：227 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-20 21:12:10
================================================================================
  Target: cluster: 面向 ScanRefer 三维语言定位，回归用户最初的点云特征更新主线，研究不同层级承担不同注意力/信息交互作用的轻量结构机制，目标 mIoU ≥ 0.51。核心路径是分层信息交互真实更新点云/超点 inst_feats，再与 query 特征共同生成 mask；不能把仅修改监督损失、沿用已有层级骨架或无效路由计算称为该主线创新。以多尺度 context-only 和 M95 为既有对照，先诊断层级互补性、局部细节及跨层信息是否真正进入 mask 特征，再依据证据选择一个可推导、可证伪的结构机制。监督与关系绑定仅作辅助诊断/匹配对照，不再取代主线。覆盖机制对照、泛化稳健性和同口径效率验证；已有收益不证明新的分层注意力有效，也不自动重开历史失败或禁止的路线。

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
| server-3 | 1 | 未知 | 未知 | 未知 |
| server-4 | 0 | 未知 | 未知 | 未知 |
| server-4 | 1 | 未知 | 未知 | 未知 |
- 可用 GPU：未做实时占用确认，不能据此分配。
- 监控摘要（begin 已执行，不再重复探测）：
```text
================================================== 2026-10-20 21:12 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  无训练进程

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 withdrawn=6
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| 无 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 队列无登记运行；远端进程须另核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 0（运行 0 / 认领 0 / 等待 0）；目标 3；准入预算 3。
- 研究储备 2 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 5、待资源 0、未分类阻塞 2。
- 非终态候选与排队项合计 7；总上限 8。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 126：complete=28 / rejected=91 / blocked=7。
- 否决范围：unclassified=91；实现修订累计 9；收据文件 10（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| hierarchy-cross-leaf-physical-contact-exchange | Ask once for scoped evidence-archival classification repair and one extra bounded SAME-PCE implementation revision. Tests are RUN/failed; revision2 result_field pending is an explicit archival hold, not an unrun test or scientific PASS. Preserve all hashes/timestamps/failures, no automatic revision3/training. | 2026-10-20T11:13:32.144632+00:00 |

## 4. This Tick's Actions
- 仅处理 cluster_project；已核实实际所属任务和最新目标、资源、授权。快照为 2026-10-20 21:12:11 上海时间，模式 design。目标 0.5100，历史最佳 M95 为 0.5020，差距 0.0080；没有新的训练指标。
- 复用 begin 的唯一预检：运行、认领、排队均为 0，未列操作异常；授权 GPU 的利用率、显存和独占状态未知，不据此推断空闲。未重复 monitor/goal，未使用 GPU，未操作其他项目或调度。
- 按紧凑视图、分页和稳定 ID 核对七个到期候选。四个辅助监督候选仍为主线优先级保留；两个原生数值诊断仍需新的可区分测量方案，未出现新证据，未重复已失败的同指针或克隆探针。未声称全部独立研究路线已穷尽。
- PCE 的两次实现修订已用尽。修订 2 原生测试已经运行且完整源码数值控制失败；pending 仅表示不可变预注册源码证据与结果时间检查之间的归档冲突，不是未测试或科学通过。2026-10-20 21:14:41 上海时间核对指定授权唤醒文件仍不存在，本会话也没有新增无歧义许可；到期和心跳不构成授权。
- 本轮仅完成状态复查和审计留档，没有新模型/配置、诊断实验、候选、准入、提交、推送、部署、入队或训练。实际产出是本轮快照、完整六段报告及七段短记忆续接；科学状态未变。报告时尚未通过 finish，不能称本轮完成。
- 用量以本轮实际收据为准，报告生成时未知；可见窗口仅为 begin 到收据写入，不包含前置读取、晚到记录和最终回复等全部活动。缓存已包含于输入，推理已包含于输出，不重复相加，不将用量当账单。

## 5. Decisions Made
- 继续保持分层信息交互真实更新点云/超点 inst_feats 的主线，以及原科学、资源、数据、seed 和 schedule 约束；数值实现失败不是训练效果或整个机制被否定的证据。
- 储备 2/2、准备预算 0、未完候选 7/8。保留现有稳定 ID 和原负证据，不制造占位变体、不改名重开。PCE 仍等待此前已提出的有范围归档修复及额外一次局部修订许可，不重复索要 GPU 权限或催问同一确认。
- 已知相同等待状态无法满足 Capacity-gap design made no durable candidate progress，且本轮没有修复该检查的新研究进展，不重复调用相同证据的 finish，不修改校验器、时间戳、科学门槛或修订次数。保存报告后诚实 abort，并只读核实本轮租约和 pending 状态释放；未获 finish 成功就保留 INCOMPLETE。
- 无新增可操作变化，不重复通知旧阻塞。后续只在真实许可、新的区分性证据或其他合法状态变化后续做；此决定不改变调度，也不构成全局研究暂停。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
