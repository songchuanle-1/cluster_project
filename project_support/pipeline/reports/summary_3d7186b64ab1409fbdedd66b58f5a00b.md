# Research Pipeline Report - cluster_project
快照时间：2026-10-15T12:09:53.215043+00:00；生成报告时快照年龄：249 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-15 20:09:52
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
| server-4 | 0 | 未知 | 未知 | 未知 |
- 可用 GPU：未做实时占用确认，不能据此分配。
- 监控摘要（begin 已执行，不再重复探测）：
```text
================================================== 2026-10-15 20:09 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.194) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  无训练进程

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

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
- 活跃 0（运行 0 / 认领 0 / 等待 0）；目标 1；准入预算 1。
- 研究储备 5 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 候选累计记录 100：blocked=5 / rejected=91 / complete=4。
- 否决范围：unclassified=91；实现修订累计 0；收据文件 5（含修订或重试，不代表成功率）。

## 4. This Tick's Actions
- 快照2026-10-15T12:09:53.215043+00:00，design；仅续做到期主线m95-hierarchical-mask-feature-path-audit。begin已做一次监控和目标检查；没有重复预检。归属核实，Pipeline-cluster_project为Disabled，目标20约束/11禁令和server-4唯一GPU0授权未改。
- 2026-10-15T20:12:07.418243+08:00新鲜资源复查：GPU0总32607、已用23891、空闲8211MiB、利用率79%；PID2634704 uses20016MiB; PID3267122 uses3776MiB。原训练锁仍被持有，另两诊断锁实际取得并释放；无其他NVML上下文、至少30000MiB余量、三锁全取得三项原守卫均false，未分配GPU。
- 相对18:14历史观察，现有资源证据显示两个NVML上下文、空闲显存更少；这没有解除主线原生捕获阻塞，也不证明本项目训练运行。未读取占用进程的作业内容，未发信号/reset/删锁。
- 源码/固定TRAIN输入/严格checkpoint装载及构造对照此前已完成，未重复制造同等证据。真实学习特征的层级互补/冗余、padding任务伤害及新机制收益仍未知。保留此前两次严格数值控制FAIL。
- 同一主线候选追加4条哈希证据，科学状态blocked/inconclusive，六项准入仍false；其余99记录及4个辅助监督范围暂停原样保留。储备5/目标2/预算0，不增加储备、重启M201或改监督主线。
- 新增候选/训练变体/准入/GPU分配/原生forward/backward/优化器步数均0。执行状态待finish及实际释放核验。收据仅统计begin至receipt可见的本地部分用量，缺失记未知；缓存已包含在输入、推理已包含在输出，不重复相加、不作账单。

## 5. Decisions Made
- 依据原始资源和锁的实际失败，以external_resource_blocked有界收尾；不放宽独占/30000MiB/科学准入门槛，不为填槽制造调参、归一化或监督候选。历史M95仍0.5020，目标0.5100，本轮没有新的性能结果。
- 原生特征捕获仅在新鲜固定身份、无其他NVML上下文、显存及原三锁全部通过后执行。下一候选复查条件为2026-10-15T21:12:07.418243+08:00或真实资源/目标/授权变化；这不是保存的自动化触发时间，准确调度时间未知。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
