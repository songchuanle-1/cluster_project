# Research Pipeline Report - cluster_project
快照时间：2026-10-13T20:24:14.179056+00:00；生成报告时快照年龄：3207 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-14 04:24:13
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
================================================== 2026-10-14 04:24 : cluster_project ==================================================

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
- 本轮项目为 cluster_project，design 模式；复用04:24:14+08快照，不重复preflight。截止05:24:14+08保持不变。科学状态validation；实际finish exit1，CLOSURE_INCOMPLETE: Capacity gap remains with executable research，四个候选仍validation导致提前收尾不被接受。本轮执行状态INCOMPLETE，租约仍在，确切token的abort和释放核验随后进行。
- 已执行不可变V2八组32表达的匹配控制；性能归因132次原生前向/反向定位无事件和重复物理参照对开销。只优化无事件路径与单次场景内对称参照对复用，不改损失、数值配置或推理路径。
- 14组原版/优化版原生字段、描述符、损失及梯度比较全部差异0；优化版18组36次完整TRAIN前向/反向、36输出字段和参数梯度重复差异0；8组活动分量触达498个原有参数张量，新增可训练参数0。
- 优化版八组匹配控制通过，所有语义控制行和推理指纹与V2完全相同。13组52项原生CPU几何变换，版本差异0，最大不变性误差1.12923e-7，调用后恢复完全一致；不冒充全模型语义变换不变性。
- 三项统一VAL推理资源测量及九项TRAIN路径测量完成；均warmup20/repeat100，输入/协议/checkpoint经程序配对。候选9.762532428G/157484090参数/70.3697ms/1008.8516MiB；相对冠军0G/0参数/+7.9444ms/+3.3625%显存，相对baseline+.061656064G/+1578239参数/-37.6480ms/+2.8877%显存。
- TRAIN最坏输入候选540.069ms/冠军397.051ms，显存+1.3629%；无事件402.915/412.842ms，显存+1.0685%；单场景有效事件260.458/257.807ms，显存+.7010%。共有360次测量推理及1080次资源前向/反向；FLOPs跟踪实际前向次数未知。共享测量不宣称隔离加速。
- 服务器最新观测2026-10-13T21:16:40Z（北京时间05:16:40）；das/GPU7身份正确，利用率0%，943/81559MiB、空闲80137MiB；外部PID262355/python/928MiB保留，两把诊断锁可重新获得。本地时钟不同，未把服务器时间当本地截止。
- 六项执行门槛diagnosis/controls/native_backward/resources/independence/constraints均通过，18约束/11禁区保持；trained mIoU、真实参照身份及穷尽新颖性仍未知。0optimizer更新、0提交、0训练准入凭证、0训练启动。
- 保留初始UTF8静态适配失败与缺失暂存协议的真实失败记录；补齐哈希正确的原协议和候选YAML后另用新日志重试成功，不改阈值。原有PDC及无关改动未触碰。
- finish失败收据截至05:15:49+08为partial_window：79条调用记录，输入13927539、输出79823；缓存输入13411200已包含于输入，推理输出38046已包含于输出，不重复相加。实际记录0新候选/4候选更新/21新证据引用/0准入或训练。abort收据会更新此窗口；窗口仅含begin后至收据的本地记录，不含前期读取、迟到记录或最终回复，不作为账单。四条记录是同一BPS路径加三条旧诊断关联，不冒充四个独立新机制。

## 5. Decisions Made
- 2026-10-14 05:14:26 question：BPS已完成执行验证，但流水线禁止自动git add/commit；已询问用户是否允许仅提交经过测试的BPS模型和配置，再按既有准入、ff-only同步和原生训练步验证流程继续。见pipeline/decisions/20261014-051426_question.md。
- 保留四个稳定候选ID，三项标量角色诊断只补充独立BPS路径进展和具体下一步；不覆盖其原始gate、失败或来源事实，不重跑校准、不伪造否定、不凑第二变体。
- 等待明确的限定范围提交授权不是显存阻塞。postflight已实际拒绝当前诚实的提前收尾，原始错误已保存在bps_postflight_failure_c9de23ffb1804f1eaa81cf54b94b9d6a.md；不重复finish、不等到截止、不延长截止、不伪造阻塞或冷却，随后abort确切token并核验释放。
- 下轮具体时间未知，以已保存自动化为准；本轮不修改任何项目调度、目标、准入门槛或资源白名单。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
