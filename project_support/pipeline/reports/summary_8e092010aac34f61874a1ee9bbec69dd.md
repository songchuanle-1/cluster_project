# Research Pipeline Report - cluster_project
快照时间：2026-10-28T12:09:46.800448+00:00；生成报告时快照年龄：2102 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-28 20:09:46
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
================================================== 2026-10-28 20:09 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  无训练进程
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hpc] 进程未见 (deathwatch 1/3) — 暂不处置

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 running=1 waiting=1 withdrawn=6
    待推: [M206-CGCA] configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml gpu=1
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M218-HPC | configs/Quard/ctf_hcg_csort_hpc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hpc.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
- 活跃 1（运行 1 / 认领 0 / 等待 1）；目标 3；准入预算 2。
- 研究储备 1 / 2；储备准备预算 1，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 6、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 1；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 145：complete=39 / rejected=94 / blocked=10 / training=1 / validation=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 13；收据文件 24（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| hierarchy-coarse-conditioned-fine-channel-attention | Preserve manually paused M206 and full epoch24 checkpoint. Do not resume/migrate/cold-start on any GPU without a later explicit human instruction; GPU1 remains released to others. | 2026-10-22T16:24:16.243554+00:00 |
| hierarchy-parent-butterfly-token-composition | Preserve original BFC crash and verified epoch19 last checkpoint; exact checkpoint best .4992169439792633 is distinct from rounded terminal-log .499. Diagnose failing data tensor overlap, then complete concrete source-compatible recovery plan and BFC-specific human resume authorization. Only GPU0 is now allowed; do not use GPU1, cold restart or borrow HAP/M206 grants. This hold never blocks CTS. | 2026-10-26T09:04:54.984472+00:00 |

## 4. This Tick's Actions
- HPC/M218已canonical stopped_unknown：原PID187081 absent，最后TRAIN2/50 3687/4686，仅epoch1 val exact.2810768485069275/printed.2811，archive73ba99a73d394a37a41dc431277a3543；无earlystop/exceptionmarker，原因UNKNOWN，不作正常结束/OOM/机制否定/恢复推断。
- APF实际分支launched：Actual four-arm technical admission and single canonical launch verified; efficacy UNKNOWN.
- 唯一已验证训练M219-APF GPU0 PID793277/start80769230，source/runtimed0e2f95712ed16446907706fbf6a65d34996a9ad；根2026-10-28T12:41:00.042148+00:00 TRAIN1/50 245→254/4686。
- 上海时间2026-10-28 20:41，M219-APF原进程793277/start80769230在server4物理GPU0真实TRAIN1/50从245增长到254/4686；尚无原生验证mIoU，最佳值未知。
- APF本轮真实原生检查：同两批自然TRAIN、公共835个具名参数含shape与初始化指纹相等；每步2048真fine路径、单factor/GELU及两次原mean参与原loss反传，整体factor权重两步实际更新。逐块/行/调用为描述，不添加非零门。
- 原资源口径bs1/lang1/warm20/repeat100：APF计数FLOPs9.741560908G、参数156497978；对照9.762532428G/157484090。中位35.508416→37.065783ms（慢4.39%），P9037.215594→39.411110ms（慢5.90%）；allocated936763392→932073984（低0.50%），reserved1191182336→1184890880。完整unsupported记录保留，纯TRAIN峰值和完整未计数开销仍未知。
- 实际四臂独审、准入收据、唯一canonical派发/唯一Popen和原进程增长均有当前哈希证据；本轮1个既有APF准入并启动，0新候选/0模型修订。

## 5. Decisions Made
- 原source/null/protocol/旧负证据不改；0新候选/0模型修订，未由记录器启动/恢复任何任务。
- HPC原因UNKNOWN；APF收益UNKNOWN。只实际证据可说明技术准入/launch，不借用旧PASS或推测终态。
- 按实验优先推进已有APF至实际训练；不把剩余准备预算写为已耗尽，不宣称设计路线穷尽或设置无收益冷却。后续就绪储备不足仍按新快照继续独立实验准备。
- APF技术准入不证明精度上涨；实际推理时延较慢如实保留。HPC原因UNKNOWN，仅首轮验证.2811且训练未完成；既有技术证据和原收据保留，旧恢复边界不变。GPU1禁用、M206暂停、资源授权和调度未改。
- 本地只读进程起点采集首稿在SSH前因字符串空字符被拒绝，另存v2修正后成功核原PID；未重放任何远端训练请求或派发。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
