# Research Pipeline Report - cluster_project
快照时间：2026-10-14T20:09:59.034382+00:00；生成报告时快照年龄：103 秒；模式：event

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-15 04:09:58
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
| server-4 | 0 | 未知 | 未知 | 未知 |
- 可用 GPU：未做实时占用确认，不能据此分配。
- 监控摘要（begin 已执行，不再重复探测）：
```text
================================================== 2026-10-15 04:09 : cluster_project ==================================================

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

## 4. This Tick's Actions
- 本轮event快照2026-10-15 04:09:59.034382+08，截止05:09:59.034382+08不可变。实际任务环境ID与归属一致，goalSHA24083b8d未变、19约束/11禁令/server4 GPU0单槽/后台Disabled核实。begin仅一次，章节0-3复用脚本事实表。
- 本轮new_terminal:M201-BPS与ledger_changed对应上轮已完成的误停状态纠正，不是新的停止或训练结果。当前同一实验为stopped_unknown/screen_interrupted，Best0.489848792552948@18、完成26轮/no_improve8，recovery_launch_verified=false；没有恢复训练。
- 到期候选0、未到期blocked4，运行/认领/等待均0；四工作项原retry_after为2026-10-15 04:15:14.021082+08。该资源冷却尚未到期，本轮不重复GPU拒绝、CPU恢复、旧候选审查或失败路线，不等待截止或等待重试时间制造进展。
- 上轮7db5实际finish0/CLOSURE_POSTFLIGHT_PASS/COMPLETE，收据FINALIZED/context_committed=true，03:37:45租约与pending不存在已核实。本轮只更新七段记忆的上轮收尾事实；不重复计入7+6+69测试、642优化器恢复或历史证据引用，不修改候选/门槛/实验/台账/冷却时间。
- 本轮GPU利用率/显存/实际锁占用未重测，保持未知。上轮03:29的20107MiB使用/11994MiB剩余/NVML原PID20016MiB/训练锁持有属于缓存证据，不能声明现在已释放或仍有同样占用。资源原因未解决，队列无训练不等于GPU空闲；四项科学状态仍blocked，三scalar六门槛仍false、旧FAIL保留。
- 本轮新增候选、证据引用、GPU/原生前向、参数梯度、优化器更新、准入和训练恢复均0；未新建任务、改调度、重置GPU、删除锁、使用sudo或处置其他进程。finish尚未执行，执行状态待postflight；收据为begin到收据局部窗口，数值未知不填零，缓存属于输入/推理属于输出，不将用量当账单。

## 5. Decisions Made
- 无新的科学或调度决策。沿用已核验的同一M201完整状态恢复方案及冻结epoch4四组诊断；等待原重试/真实资源解除条件，不放宽门槛、不冷启动或制造变体。
- 本轮完成已有状态纠正的报告与记忆对账后收尾，不延长04:15:14资源重试窗口。下一自动调度时间未知；目前无新的需用户处理事项，服务器侧残留排查仍是上轮已报告的条件。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
