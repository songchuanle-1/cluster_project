# Research Pipeline Report - cluster_project
快照时间：2026-10-13T21:21:23.573480+00:00；生成报告时快照年龄：169 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-14 05:21:23
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
================================================== 2026-10-14 05:21 : cluster_project ==================================================

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
- cluster_project本轮快照2026-10-14T05:21:23.573480+08:00，design模式；begin已执行唯一一次monitor和goal检查，返回码均0；实际owner环境变量与execution_mode匹配，Pipeline-cluster_project仍Disabled。原截止06:21:23.573480+08保持不变。
- 科学状态validation，未发生新的终态、准入或训练变化。按稳定ID读取BPS当前记录：沿用上一轮六项执行gate通过的证据，训练效果、真实参照身份及穷尽新颖性仍未知，不把缓存证据当本轮新实验。
- 05:22:30+08只读静态核验：BPS九个模型文件和候选YAML与已测manifest完全一致，53个已绑定证据哈希无变化。没有重复原生、匹配对照、资源或几何测试；没有改候选阶段、gate、证据清单或制造时间戳进展。
- 用户对限定范围BPS提交的明确授权仍未收到，沿用05:14:26已提出的问题，不重复提问或记录新决策。BPS模型和配置仍未提交，原有PDC用户改动保留。没有自动git add/commit、同步、入队或启动训练。
- 本轮未再次探测GPU显存或利用率，实时值未知；上一轮服务器05:16:40+08的空闲80137MiB及外部PID262355只是带时间戳的缓存事实，不用于新资源分配，也不称显存阻塞。
- 实际产出为本轮六段事实报告和运行记忆核对；新候选0、新科学证据0、原生测试0、optimizer更新0、准入0、训练启动0。四个候选仍validation。未制造no_information_gain冷却、外部资源阻塞、否定证据或截止临近条件。
- 上一轮真实finish失败条件为Capacity gap remains with executable research；当前无新增科学进展或可执行的已授权提交动作，不用未变证据重复finish。按foreground契约直接abort当前确切token；本报告写入时租约尚持有，abort结果和释放状态随后核验，不能称COMPLETED。
- 本轮收据用量尚未知，待独立abort收据；窗口为本轮begin至收据的本地响应记录，排除更早读取、迟到记录和最终回复。缓存包含在输入、推理包含在输出，不重复相加、不视作账单。上一轮用量和22条证据引用不转计为本轮产出。

## 5. Decisions Made
- 本轮无新研究决策；继续沿用已记录的限定范围提交授权问题及真实next_action，授权后才进入测试代码提交、commit/goal/source绑定准入、ff-only同步和原生训练步验证。
- 不重复完成的实验来凑进度，不放宽准入，不把未变的审批等待伪造成GPU阻塞；没有合法的早停冷却schema，因此保留未完成候选并以INCOMPLETE释放租约。
- 监测状态与先前通知相同，无新的用户事项，不重复推送相同授权提醒。下轮确切时间未知；未操作任何调度、其他项目或后台决策进程。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
