# Research Pipeline Report - cluster_project
快照时间：2026-10-12T22:13:05.386167+00:00；生成报告时快照年龄：121 秒；模式：event

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-13 06:13:04
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
================================================== 2026-10-13 06:13 : cluster_project ==================================================

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
- 快照为北京时间2026-10-13 06:13:05，event 原因是上一轮已核实的 M200-TMR 终止、活跃队列及账本变化；本轮 begin 监控与目标检查均返回0，未重复 preflight。
- 按稳定ID核对 m95-native-target-mention-role 已为 complete；复用05:17本地核实的原生终止日志及既存结果分析，不将旧证据重新计作本轮实验。M200 原生耐心10早停于23/50，最佳mIoU为0.4952795207500458（epoch13），低于冠军0.5020，目标0.5100仍未达成。
- 快照运行、认领、等待均为0，到期候选0；GPU7利用率、显存及占用未知。本轮无GPU测试、无新候选、无准入或训练启动；未改变阶段、18条约束、11项禁令、服务器或调度。
- 保留上一轮仅针对已测试前提的冷却至2026-10-13 07:00+08；本轮只接收已完成终止事件，不重新审查关闭路线，不复跑等价诊断，不声称全局路线耗尽。原始119行记忆另存 codex_memory_before_20261013_0613.md，并更新当前事件与快照。
- 执行状态须以本轮 finish 明确PASS/COMPLETE及匹配租约消失为准；收据用量窗口和记录产出待 finish 后只读核实，缺失记未知。缓存已包含在输入中，推理已包含在输出中，用量不是账单。下一调度时间未读取，未知。

## 5. Decisions Made
- M200结果已经上一轮报告，本轮没有新的科学结论；保留 complete 状态及全部正反证据，不替换冠军，不自动重启、调参或更名填补空槽。
- 当前无到期候选；按 event 模式接收终止变化并收尾。07:00是已有研究冷却截止，不是保证的自动调度时间，也不是新延长的截止；原始本轮截止仍为2026-10-13 07:13:05+08。
- 训练结果未达冠军不否认原始错根诊断；场景聚类区间、子组伤害和噪声下界仍未量化，未运行的测试仍不能称PASS。空队列不等于GPU空闲；后续资源使用仍需新的实时占用和独占租约核验。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
