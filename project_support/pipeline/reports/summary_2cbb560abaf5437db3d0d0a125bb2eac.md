# Research Pipeline Report - cluster_project
快照时间：2026-10-20T07:33:05.543921+00:00；生成报告时快照年龄：373 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-20 15:33:04
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
================================================== 2026-10-20 15:32 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [不可达]

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
- 本次执行故障（不等于缺候选或缺授权）：
| 服务器 | 实验 | 故障 |
|---|---|---|
| server-3 | 未知 | 服务器不可达，实时进程与资源未知 |
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
- 本轮仅对cluster_project执行一次前台预检和状态复核，快照为2026-10-20 15:33:05上海时间。目标0.5100，历史最佳M95为0.5020，差0.0080；没有新的研究结论。
- 最新目标哈希、25项约束/11项禁令、实际任务ID、前台归属和GPU白名单核对未变；旧后台计划仍Disabled，闭环策略仍启用。
- 快照核实active/running/claiming/waiting均0，候选准入预算3不等于有可训练候选。server3连接仍失败，未把连接失败写成GPU空闲；其他GPU占用不从缓存推断。
- PCE现为human_revision_authorization等待，实际完整源码测试已执行且失败；result字段pending仅是已有归档未定稿。归档修复及额外实现修订的人工确认尚未到达，heartbeat不是同意。未重复索要确认或执行第三次修订。
- 两个到期旧数值候选按稳定ID复核：同指针float32归约1.9073e-6仍高于原1e-6，当前无已证实的新测量修复；没有重复原样GPU测试，也未以它们冻结其他已授权主线。储备已满、reserve_budget为0，未造占位变体。
- 本轮新科学测试、模型修改、新候选、准入、入队、训练、优化器步数、提交、推送及调度修改均0。旧15:07测得的PCE588.406ms及2.8610e-6是缓存旧结果，不计本轮成果。
- 用量收据仅本轮begin至receipt的局部可见窗口，当前未知；缓存包含于输入、推理包含于输出，不重复累加或当账单。实际产出仅本轮状态复核与六段留档。

## 5. Decisions Made
- 维持已有PCE人工等待和两个数值实现阻塞，不改原失败、证据时间戳、哈希、科学门槛或修订次数。授权到达或真正新可区分证据出现才续做，不重复催问。
- 未发生真实候选进展，不伪造证据变化来满足design校验，不宣称无数独立路线已穷尽。完整报告留档，finish实际通过才能称完成；若容量缺口/进展校验拒绝真实等待，则保留证据abort并核实释放。
- 这是未变化的已报告阻塞，本轮不产生新的用户提醒，不修改automation通知策略或任何项目调度。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
