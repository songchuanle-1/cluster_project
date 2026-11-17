# Research Pipeline Report - cluster_project
快照时间：2026-10-21T08:12:37.151684+00:00；生成报告时快照年龄：187 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-21 16:12:36
================================================================================
  Target: cluster: 面向 ScanRefer 三维语言定位，回归用户最初的点云特征更新主线，研究不同层级承担不同注意力/信息交互作用的轻量结构机制，目标 mIoU ≥ 0.51。核心路径是分层信息交互真实更新点云/超点 inst_feats，再与 query 特征共同生成 mask；不能把仅修改监督损失、沿用已有层级骨架或无效路由计算称为该主线创新。以多尺度 context-only 和 M95 为既有对照，先诊断层级互补性、局部细节及跨层信息是否真正进入 mask 特征，再依据证据选择一个可推导、可证伪的结构机制。监督与关系绑定仅作辅助诊断/匹配对照，不再取代主线。覆盖机制对照、泛化稳健性和同口径效率验证；已有收益不证明新的分层注意力有效，也不自动重开历史失败或禁止的路线。

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
================================================== 2026-10-21 16:12 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mdc] Best=0.4840 16/50 no_improve=1/10 gpu=0 ? 序列: 0.4779, 0.4833, 0.4798, 0.4840, 0.4809

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 running=1 waiting=1 withdrawn=6
    待推: [M206-CGCA] configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml gpu=0
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M205-MDC | configs/Quard/ctf_hcg_csort_mdc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mdc.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
- 活跃 2（运行 1 / 认领 0 / 等待 1）；目标 3；准入预算 1。
- 研究储备 2 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 4、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 2；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 133：complete=28 / rejected=94 / blocked=8 / training=1 / deployment=1 / validation=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 12；收据文件 12（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |

## 4. This Tick's Actions
- 上海2026-10-21 16:12 begin完成监控、目标及既有队列派发检查：仅server4 GPU0容量1，M205 running、M206 waiting/ready；无终态/运维故障，reserve/creation0。M205 Best=.4840、16/50、no_improve1/10，仍低于历史M95 .5020。
- 16:13:35严格pinned主机/GPU0 UUID核验：20304MiB/util87%，M205 PID3842306原argv/cwd/starttime一致，native第16轮2354→2355/4686递增、log age0.51秒。另一CUDA context PID2589742归属未核验，不干预；GPU0未空闲。
- 同M206 waiting/GPU0/resume_waiting，无当前PID/log/claimed_gpu，launch_verified=false；两份resume证明hash匹配，running仅GPU0=M205，无dispatch_hold/admission_error。固定checkpoint存在936269892bytes，未在忙卡时重hash或载入；仍待空闲后原生epoch9 full resume。
- 本轮8旧hold到期，由独立只读复核对照既有归档，4辅助scope/2数值测量/PCE3次与RSTR2次耗尽状态未解锁，无新指定授权wake文件或修复证据。保留负结果，不重开、不改门槛、不将实现数值问题当机制证伪。
- 当前真实resource_check/blocked绑定M206与新证据；0新候选/0native诊断/0准入/0队列新增/0启动。HAP已备储备保持native UNKNOWN，未做重复staging或占用GPU1。

## 5. Decisions Made
- 保持最新仅server4 GPU0范围及M205现有运行；GPU0实际全空闲后优先M206相同实验full native --resume epoch9，启动前再核精确源码/固定checkpoint SHA并验证新PID/log/native进度。
- 本轮正常训练和相同资源等待，无新的完成、失败、用户事项或研究结论，按约定静默。早期Best变化不代表最终收益，不用训练观察选参。
- 当前reserve/creation预算0，不新建变体，不恢复旧监督主线或耗尽修订路线；不改资源/禁用项/goal/调度。完整六段审计和memory留档后实际finish，不预写PASS。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
