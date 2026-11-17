# Research Pipeline Report - cluster_project
快照时间：2026-10-13T02:12:19.944886+00:00；生成报告时快照年龄：1001 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-13 10:12:19
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
================================================== 2026-10-13 10:12 : cluster_project ==================================================

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
- 快照为2026-10-13 10:12:19+08，design模式；begin已监控及检查目标一次，运行/认领/等待均0，预算2。复用事实表，未重复preflight。
- 续做原有主角色权重和次角色正质量稳定ID，实现冻结16组64表达加原始对照的原生诊断适配器，未新建变体或占位候选。
- 首个远程CPU适配器测试退出1：旧主角色恢复操作同时把未匹配EOS权重0.1改为1，破坏无角色重叠时的无效应对照。保留失败源及全部旧证据，不再将旧梯度变化全部归因于角色重叠。
- 预注册隔离修正仅用于诊断适配器，不修改原模型。再次远程CPU测试退出0：22读数/110次Criterion调用，两次1999重复完全一致、恒等差0、梯度有限；两个无角色重叠对照隔离改动均0，旧改动均非0；冻结八个真实映射隔离梯度均变化，旧/新导数8/8不同。投影仍是合成64D，不是原生模型危害或收益。
- 快照后远程02:25:28UTC：server-6/das/GPU7 UUID核实，利用率0%、显存943/81559MiB，但PID262355仍占928MiB。原生守卫拒绝启动，输出结果及进度文件不存在；02:26:08UTC核实两个诊断锁可再次取得。远程时钟超前，分别保留本地10:22:42+08核验时间。
- 科学状态blocked；全模型原生验证未运行，六项准入门槛未通过；新准入0、训练启动0。实际finish退出1：Blocked GPU candidate lacks authorized single-task server；故障已保留，不重复同证据finish。执行状态INCOMPLETE，将对本轮确切token执行abort并核实释放；收据用量在释放后读取，当前未知。

## 5. Decisions Made
- 主角色映射覆盖13表达/17位置的事实保留，但上一轮优先级诊断梯度含EOS混杂；采用隔离对照继续同一稳定ID，不隐去旧失败或修改原模型。
- 保留三个稳定ID及原始采样/1e-6阈值，需无驻留进程且独占租约成立才续跑；11:00+08是候选重试时间，不是已核实的自动化运行时间。
- 不把简单优先级或归一化修正作为独立新核心，不为填槽训练。无全局路线穷尽声明；如两槽配置仍被单任务收尾校验拒绝，保留故障并abort，核实本轮租约释放。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
