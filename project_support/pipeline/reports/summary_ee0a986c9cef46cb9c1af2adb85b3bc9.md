# Research Pipeline Report - cluster_project
快照时间：2026-11-06T07:12:40.563873+00:00；生成报告时快照年龄：635 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-11-06 15:12:39
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
================================================== 2026-11-06 15:12 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mic] Best=0.4988 25/50 no_improve=8/10 gpu=0 ? 序列: 0.4953, 0.4950, 0.4901, 0.4880, 0.4867

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 running=1 waiting=2 withdrawn=6
    待推: [M206-CGCA] configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml gpu=1
    待推: [M227-LFT] configs/Quard/ctf_hcg_csort_lft/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_lft.yaml gpu=1
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M229-MIC | configs/Quard/ctf_hcg_csort_mic/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mic.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
| 2 | M227-LFT | configs/Quard/ctf_hcg_csort_lft/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_lft.yaml | waiting | - | server-4 |
- 活跃 1（运行 1 / 认领 0 / 等待 2）；目标 3；准入预算 2。
- 研究储备 2 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 7、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 2；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 157：complete=49 / rejected=94 / blocked=11 / training=1 / validation=2。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 13；收据文件 35（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| hierarchy-coarse-conditioned-fine-channel-attention | Preserve manually paused M206 and full epoch24 checkpoint. Do not resume/migrate/cold-start on any GPU without a later explicit human instruction; GPU1 remains released to others. | 2026-10-22T16:24:16.243554+00:00 |
| hierarchy-parent-butterfly-token-composition | Preserve original BFC crash and verified epoch19 last checkpoint; exact checkpoint best .4992169439792633 is distinct from rounded terminal-log .499. Diagnose failing data tensor overlap, then complete concrete source-compatible recovery plan and BFC-specific human resume authorization. Only GPU0 is now allowed; do not use GPU1, cold restart or borrow HAP/M206 grants. This hold never blocks CTS. | 2026-10-26T09:04:54.984472+00:00 |
| hierarchy-nonlinear-lifting-analysis-synthesis | Preserve LFT manually paused checkpoint22, original source4457, receipt and paused_run. No resume, migration or cold start until later explicit human authorization; GPU1 remains excluded. WFC alone continues GPU0. Paused research stage is blocked/human_authorization. | 2026-11-04T08:16:35.222364+00:00 |

## 4. This Tick's Actions
- canonical begin无新启动/终态/异常；2026-11-06T07:14:56.367090+00:00同MIC PID2881795/start152216088/source07ef在server4物理GPU0原生TRAIN epoch25步3272→3276/4686，原cwd/argv/stdout日志匹配，未见fatal标记。
- 一次只读确认原CPUguardian3033165/start152434416存活且持training/diagnostic/exclusive三条当前内核FLOCK。未续写旧lease/binding、未重启训练或守护；保存HVD项目max1真实资源阻塞。
- 本轮preflight报告epoch25/50，阶段验证舍入值0.4953/0.4950/0.4901/0.4880/0.4867，阶段best0.4988/noimp8；终态精确best未知，不作效力或novelty结论。
- 本地独立只读审及root核对main07ef、完整index、20用户脏文件和9项目文件保持；HVDd20/PSCa709版本记录及原冻结审保持，未重跑源测试。M206/LFT人工暂停，GPU0共享授权、目标、bans、策略及Disabled调度不变。

## 5. Decisions Made
- MIC占唯一项目GPU0槽及三锁；当前训练后余12802MiB低于原新任务20000MiB。HVD优先PSC等待自然释放，两者native/resources NOT_RUN。外部共享许可继续有效，不要求空卡/无context/低利用率，不重复询问许可。
- 储备2/目标2、creation_budget0，本轮0新候选/0准入/0GPU模型检查/0训练或guardian启动；复用既有源及受审冻结包，不补签旧NULL、不改原协议和调度、不恢复暂停项。
- 继续观察同一MIC完整验证及自然终态，既有guardian随精确trainer自然退出释放。保存真实资源阻塞后按契约report/finish；健康状态且无用户可行动变化时静默。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
