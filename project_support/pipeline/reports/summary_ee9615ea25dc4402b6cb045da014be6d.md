# Research Pipeline Report - cluster_project
快照时间：2026-10-13T05:09:27.565499+00:00；生成报告时快照年龄：94 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-13 13:09:26
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
================================================== 2026-10-13 13:09 : cluster_project ==================================================

--- local (192.168.1.175) ---
  [不可达]

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
- 仅处理cluster_project；实际任务ID与最新foreground owner一致，目标/18项约束/11项禁令及server-6 GPU7双槽授权不变，Windows后台保持Disabled。begin在2026-10-13 13:09:27+08生成design快照，监控及目标检查各一次；运行/认领/等待均0，容量/预算均2，目标尚未达成。
- 先读紧凑视图，再按稳定ID核对三个到期候选的假设、匹配对照、原生下一步及六项未通过门槛。保留EOS混杂纠正和隔离对照、原冻结清单及1e-6阈值，不创建占位路线或改名变体。
- 本轮远程05:13:20UTC只读资源确认：das/GPU7 UUID一致，0%利用率，943/81559MiB，驻留PID262355/python/928MiB，与前轮相同。本地核验13:09:55+08；远程时钟超前，分别保留。项目空槽不等于物理卡独占空闲。
- 三个原生验证仍blocked；未启动GPU诊断或新训练，未重复不变CPU测试/路线审查，未驱逐驻留进程或操作其他项目。此恢复条件检查不算科学进展，也不宣称全局CPU路线穷尽。
- 当前closure.py哈希及521-522行条件未变，仍要求单任务服务器，而授权为双槽；真实独占资源处置无法通过已知检查。没有具体修复，不重复同证据finish，不放宽政策/门槛，不称完成；本轮执行状态INCOMPLETE，保存证据后abort确切token并核实释放。
- 复用脚本六段及事实表，未读取完整快照/历史或重复preflight。收据用量窗口与实际产出待abort后读取，目前未知；缓存包含在输入、推理包含在输出，不重复相加，不是账单。

## 5. Decisions Made
- 无新科学决策；保留三个稳定ID及冻结原生验证条件，保持科学状态blocked；不把资源记录刷新当作候选进展或准入。
- 14:00+08仅为候选重试时间，不是已核实的自动化时间，也不是成功收尾冷却；不修改任何调度。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
