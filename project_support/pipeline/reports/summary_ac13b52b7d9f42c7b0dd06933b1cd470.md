# Research Pipeline Report - cluster_project
快照时间：2026-10-13T22:10:31.567626+00:00；生成报告时快照年龄：178 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-14 06:10:31
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
================================================== 2026-10-14 06:10 : cluster_project ==================================================

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
- cluster_project本轮快照2026-10-14T06:10:31.567626+08:00，design模式；begin唯一一次monitor和goal检查均返回0。实际任务环境ID与execution_mode绑定一致，Pipeline-cluster_project为Disabled。实际截止07:10:31.567626+08不改写。
- 快照运行0、认领0、等待0，目标容量2，预算2；四个due稳定ID保持validation。BPS六项执行门槛仍为上轮已验证状态，不冒充本轮新实验；训练mIoU、真实参照身份及穷尽新颖性仍未知。
- 06:12:04+08完成只读静态完整性核验：九个BPS源文件、候选YAML和53个绑定证据哈希均与已测版本一致。Git HEAD仍810f3067b22692f2cdc1b096b4b7d5931bacd238，BPS模型和配置仍未提交，原有PDC用户修改未触碰。没有新增科学进展，不把哈希复核或时间戳更新算作研究证据。
- 限定范围提交的明确授权仍未收到，沿用05:14:26已有问题和稳定next_action，不重复催问，不自动git add/commit，不同步、准入或启动训练。没有重跑完整原生、匹配对照、几何或资源实验，没有改gate、候选阶段或证据列表。
- 本轮未额外测量GPU利用率/显存，实时值未知。以前05:16:40+08的server-6 GPU7空闲80137MiB及外部PID262355是缓存事实，不当作当前测量或新分配依据；没有将审批等待伪装成显存不足。
- 本轮实际产出是六段快照报告和运行记忆核对：新候选0、新科学证据0、原生或CPU行为测试0、optimizer更新0、准入0、训练0。上一轮66acc收据为INCOMPLETE且候选/证据变化均0，abort确实释放，非后台仍运行。
- 未变证据无法修复已知Capacity gap remains with executable research收尾限制；不重复finish、不填造早停schema、不等到截止或伪造冷却/资源阻塞。当前报告写入时租约持有，随后abort本轮精确token并核验释放；执行状态应为INCOMPLETE而非COMPLETED，科学状态仍validation。
- 收据用量窗口为本轮begin至独立abort收据的本地响应记录，用量在报告写入时未知；不含更早读取、迟到记录和最终回复。缓存属于输入、推理属于输出，不重复相加、不视作账单，也不转计前两轮用量或产出。

## 5. Decisions Made
- 本轮无新研究决策，继续保留四个稳定候选的来源事实、失败和下一步。待明确限定范围提交授权后，才推进经过测试的代码提交、commit/goal/source绑定准入、ff-only同步和原生训练步验证。
- 审批等待状态与上轮通知相同，不重复已完成的诊断来制造进展，不修改调度、其他项目、目标、seed、schedule、白名单或科学门槛。
- 不重新通知同一未变化事项；下轮具体时间未知，以已保存自动化为准。收尾完整报告保留在当前token对应文件，最终执行状态依据abort和锁核验。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
