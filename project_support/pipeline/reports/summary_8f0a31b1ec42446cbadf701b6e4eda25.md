# Research Pipeline Report - cluster_project
快照时间：2026-10-13T13:11:16.572299+00:00；生成报告时快照年龄：133 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-13 21:11:15
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
================================================== 2026-10-13 21:11 : cluster_project ==================================================

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
- 仅处理cluster_project；实际任务ID与foreground归属一致，18项约束/11项禁令未变，Windows后台Disabled。快照2026-10-13 21:11:16+08，design；运行/认领/等待均0，容量/预算均2；监控与目标检查各一次，目标未达成。
- 先读紧凑视图，再按三个稳定ID核对假设、匹配对照、冻结原生下一步及六项未通过门槛。21:00重试已到期；due0不代表测试完成。bootstrap提示不能使重复占位候选成为科学进展，本轮未建立新候选，也不声称满足科学闭环。
- 远程13:15:14UTC实测das/GPU7正确UUID，0%利用率、943/81559MiB、PID262355/python/928MiB。本地核验21:11:50+08，分别记录两个时钟；资源阻塞未变，项目空槽不是物理卡独占空闲。
- 三个原生验证仍blocked；新增科学测试/变体/准入/训练均0。不重复不变CPU测试，不驱逐驻留进程，不宣称全部非GPU路线穷尽。实际产出仅资源证据、三个候选阻塞记录及报告。
- closure.py521-522单任务条件及源码哈希未变，与授权双槽的既知收尾冲突仍在。无具体修复，不重复finish，不改变政策或准入。执行状态INCOMPLETE；保存证据后abort确切token并核实释放。
- 收据用量窗口及计数待abort后读取，当前未知；不含begin前读取、晚到记录及最终回复。缓存属于输入、推理属于输出，不重复相加，用量不是账单。

## 5. Decisions Made
- 没有新科学决策；保持稳定ID、冻结测试和所有门槛，科学状态blocked。资源证据刷新不算候选科学推进。
- 22:00+08仅为候选重试时间，不是成功收尾冷却或已核实的下次自动化时间；不操作调度。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
