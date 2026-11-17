# Research Pipeline Report - cluster_project
快照时间：2026-10-15T15:08:31.203233+00:00；生成报告时快照年龄：173 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-15 23:08:30
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
================================================== 2026-10-15 23:08 : cluster_project ==================================================

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
- 快照2026-10-15T15:08:31.203233+00:00，design；仅续做到期主线m95-hierarchical-mask-feature-path-audit。begin监控/目标检查各一次；归属匹配、旧后台Disabled；目标20约束/11禁令、server-4唯一GPU0授权及主线优先级不变。
- 新鲜固定主机/GPU身份资源复查：2026-10-15T23:10:49.485691+08:00 total32607/used31815/free287MiB/util64%; PID2634704 uses20016MiB; PID4093981 uses11700MiB; cluster_project_gpu0_m201_migration.lock:held_by_existing_owner; cluster_project_gpu0_exclusive.lock:acquired_for_probe; cluster_project_gpu0_parameter_transport.lock:acquired_for_probe。原始守卫结果{"all_three_original_flocks_acquired": false, "idle_equivalent_free_at_least_30000_mib": false, "no_other_nvml_context": false}；探针取得的锁已释放，未分配GPU、发信号、reset或删除锁。该占用证据不等于本项目训练运行。
- 源码路径/固定TRAIN输入/严格checkpoint装载及构造对照已完成；本轮不重复无新增信息的CPU测试。真实学习特征的层级互补/冗余、padding任务伤害、新颖性与训练收益仍未知，既有数值FAIL原样保留。
- 主线追加4条证据引用并保留blocked/inconclusive、六项准入false；其余99条记录及四个尚未到期的辅助监督范围暂停不改。不恢复M201，不为填槽构造监督/归一化/纯调参变体。
- 新增候选/训练变体/准入/GPU分配/原生forward/backward/训练/优化器步数均0；实际产出仅一次到期资源/锁复查。执行状态待finish和实际释放核验，科学状态blocked。
- 收据用量仅begin至receipt的可见本地部分窗口；缺失记未知。缓存已包含于输入、推理已包含于输出，不重复相加或作为账单；记录变更数不等于科学收益。

## 5. Decisions Made
- 依据真实资源守卫失败，以external_resource_blocked有界收尾；不放宽独占/显存或科学准入门槛、不等待截止凑时长。M95历史仍0.5020，目标0.5100，本轮无新性能结果。
- 主线候选复查条件为2026-10-16T00:10:49.485691+08:00或真实资源/目标/授权变化；到期不能替代新鲜身份/NVML/显存/原三锁核验。辅助授权冻结与既定复查条件保持；准确的下一自动化触发时间未知，上述不是调度时间。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
