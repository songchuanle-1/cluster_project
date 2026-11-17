# Research Pipeline Report - cluster_project
快照时间：2026-10-14T04:09:55.628596+00:00；生成报告时快照年龄：3170 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-14 12:09:55
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
================================================== 2026-10-14 12:09 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.194) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-6 (100.64.3.28) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps] Best=0.4091 4/50 no_improve=0/10 gpu=7 ? 序列: 0.3077, 0.3769, 0.4091

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
- 本轮续用原租约；设计快照2026-10-14 12:09:55+08，截止13:09:55+08不变。归属、GPU7两槽、18约束/11禁令核实；后台Disabled；原用户PDC修改哈希未变。
- 三项远端CPU诊断执行返回0，CUDA隐藏/两线程：冻结TRAIN目录416场景1498表达式1502事件，108几何可用/1390不可用；25类别未知、34无同类替代；49表达式/40场景237物理掩码读数，202零/35非零，GT-self108全零。
- 配对coherence原始臂精确复现237/237；55精确差异，44超过1e-6，其中coherent-minus-fragmented正4/负40；非零数35对62。GT-self两臂全零；GT减除后没有统一单调关系。
- GT最小代价配对oracle保留精确并列、不调容差；237原始臂复现，69差异超过1e-6；53原始零转正，23表达式/19场景；oracle88非零，49GT-self全零。不是已验证见证、模型输出或可部署效果。
- 原生捕获V1缺state_dict，V2严格加载遇position_ids/token_type_ids多余键，均在前向前失败；成功前向/优化器步均0，完整stderr保留。冻结epoch4 checkpoint best_miou0.4201701879501343；没有创建/执行V3。
- 补充只读资源/训练/三锁核验见release_audit.json；本地与远端时钟分列。外部PID262355不动；无新增模型、准入或训练。M201仍训练；未把GPU锁可用当作独占。
- 本轮执行状态INCOMPLETE（尚未abort，实际结果在任务最终报告核实）；科学状态BPS=training/补充diagnosis，三scalar=validation且既有FAIL未变。既知closure Unfinished candidate made no durable progress未修复，不重复相同finish，不假造闭合/冷却。用量及产出等待收据，未知不记0。

## 5. Decisions Made
- 此前67物理掩码全零仅为有限样本；本轮35非零否定全局全零外推。coherence/GT-pair均有信息增益，但不证明真实模型伤害、收益或独立修复，不新增训练变体。
- 保留现有M201训练及原seed1999/epochs50/max_iters70/收敛规则。下一次有租约且时间充足时先预注册两缓存buffer精确相等核验，其他权重仍strict=True，再续同一冻结checkpoint的原生捕获与1e-6复现检查；不改正在训练的模型。
- 可用显存不是科学准入。没有全路线耗尽或资源阻塞证据；不能把同一机制三探针包装成两独立路线获得冷却。保留真实证据后精确abort并核实释放；下一调度时间未读取，未知。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
