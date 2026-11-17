# Research Pipeline Report - cluster_project
快照时间：2026-10-14T05:09:28.279988+00:00；生成报告时快照年龄：1996 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-14 13:09:27
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
================================================== 2026-10-14 13:09 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.194) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-6 (100.64.3.28) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps] Best=0.4202 5/50 no_improve=0/10 gpu=7 ? 序列: 0.3077, 0.3769, 0.4091, 0.4202

--- 队列: cluster_project ---
  server-4: done_earlystop=24 withdrawn=6
  server-6: done_earlystop=4 running=1
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M201-BPS | configs/Quard/bps/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps.yaml | server-6 | 7 | 未知 | 未知 | 未知 | 未知 | 未知 | running |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 1（运行 1 / 认领 0 / 等待 0）；目标 2；准入预算 1。

## 4. This Tick's Actions
- 本轮design快照2026-10-14 13:09:28+08，截止14:09:28不变；归属/GPU7两槽/18约束11禁令及后台Disabled已核实。原用户PDC哈希未变。
- 修复仅诊断工具：两个具名buffer形状类型逐值相等，扰动负对照被拒绝；其余1163状态项仍strict=True。原V1/V2及失败原样保留，冻结epoch4 checkpoint SHA=f17f2ec3...，best_miou0.4201701879501343。
- 原生BPS捕获48组/40场景/192表达式输入，96次前向；mask/loss重复最大差0.0/0.0，分解最大差1.02e-08；失败0/0。262匹配事件查询，26oracle差异超过1e-6，其中20零转正；不是见证标签或收益。
- 三旧scalar稳定ID续做固定25组/97表达式/50前向：原始MAIN-secondary92及REL-OTHER46均吸引；fractional199中27排斥，分母条件变为73排斥/46符号变化；identity及原生重复通过，旧M95失败不覆盖，六准入门槛仍false。
- 完整查询库诊断状态completed，执行返回0；明细及分母见summary.json。原始关系组件照常返回criterion，oracle仅作诊断；无优化器/模型参数反向/新增模型/准入/启动。
- 本轮后续实时训练、显存、外部进程及三诊断锁核验见resource_audit.json，本地与远端时间分别记录。所有远端诊断已结束；M201训练不重启。
- 科学状态BPS=training/补充diagnosis，三scalar=validation且缺独立结构；本报告尚未postflight，执行结果及用量等收据后在任务报告补充，未知不记0。
- 完整原生库24576查询中，50表达式有几何/6400查询、142表达式无可用cost；5389低于IoU.5，其中2907原始cost精确零、2155在oracle下超过1e-6。TRAIN indication选择106/192低IoU，其中86库内存在>=.5掩码；不是部署VAL或同类误绑定计数。
- CPU排序筛查：原V1场景元数据IndexError保留，V2只修每组单sceneID索引。50表达式40场景203048非同IoU查询对；原1e-6口径2645同向变反向/11923反向变同向，否定普遍不恶化保证。查询对相关，非独立样本/训练效应；全过程不改loss或gate。
- 实际finish返回1：Capacity gap remains with executable research: m95-native-relation-other-sign-conflict,m95-native-main-role-weight-precedence,m95-native-secondary-positive-mass。四个候选新证据均通过哈希校验，但容量缺口/未完研究仍拒绝；执行INCOMPLETE，租约保留，精确abort及释放核实随后执行。

## 5. Decisions Made
- 新checkpoint读数不等于旧M95校准结果，更不等于效果；不启动优先级/归一化调参，不改变历史失败、科学门槛或M201训练。
- 保留诊断性GT最小配对与真实见证/部署效果的区别；查询库低IoU+零损失不自动等于同类误绑定或任务伤害。后续需要冻结任务层匹配对照及原VAL评估。
- 本轮确有四个稳定候选的真实新证据；若收尾仍因容量缺口/未完研究拒绝，保留具体错误，不伪造耗尽/资源阻塞/冷却，不等待凑截止。下一自动调度时间未读取，未知。
- 两种排序变化并存，拒绝GT最小配对oracle天然改善目标质量排序的普遍主张；不是否定全部教师监督，也不是BPS训练终态。当前缺独立结构/任务层因果对照，不凑新的训练变体。
- 不重复同一finish失败，不把标量诊断完成冒充新结构准入；原始截止仍14:09:28，无资源阻塞/全路线耗尽/冷却声明。保留具体验收错误并abort；M201训练继续，实际释放/用量只在任务最终报告补充。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
