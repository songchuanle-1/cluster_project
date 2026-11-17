# Research Pipeline Report - cluster_project
快照时间：2026-10-24T16:06:44.679939+00:00；生成报告时快照年龄：1477 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-25 00:06:44
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
================================================== 2026-10-25 00:06 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  无训练进程
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psnc] 进程未见 (deathwatch 1/3) — 暂不处置

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
| M210-PSNC | configs/Quard/ctf_hcg_csort_psnc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psnc.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
- 活跃 1（运行 1 / 认领 0 / 等待 1）；目标 3；准入预算 2。
- 研究储备 0 / 2；储备准备预算 2，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 5、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 0；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 137：complete=32 / rejected=94 / blocked=10 / training=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 12；收据文件 16（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| hierarchy-coarse-conditioned-fine-channel-attention | Preserve manually paused M206 and full epoch24 checkpoint. Do not resume/migrate/cold-start on any GPU without a later explicit human instruction; GPU1 remains released to others. | 2026-10-22T16:24:16.243554+00:00 |

## 4. This Tick's Actions
- 核验actual owner/target、canonical前台规则/experiment-first及最新memory、goal/SERVERS/WindowsDisabled，前f34已释放后一次begin，原deadline不延长。
- 原PSNC进程已自然结束；只读双核精确原log/emptyGPU0，完整本远日志hash一致；canonical finalize_task done_earlystop31/.5001，原source43/receipt406/launchhistory与M206保护，独审29项。
- 复用既有BTC00e完整工具，fresh owner/assets/runtime43/UUID0/idle/三锁后stage；实际M95/BTC TRAIN2及原资源pair四请求terminal/rc0，全result身份与本地原raw只读reconcile，无重放/kill/续lease。
- BTC实际两批/common843初始化配对；每forward64个n>=3父组、proper-inside原loss梯度及三map/FFN0,2更新、原HCG-inst路径；9.758338124G、参数-131584，median慢13.3134%/P90慢19.3694%，显存15%条件未触发，未知项保留。
- 原main43→已测00e仅9新增ff-only，28dirty/untracked字节和status及空index保持；3标准/receipt9375与canonical admission/budget通过，独审133+39项。唯一canonical派发安全sync后启动BTC，2026-10-25 00:25:14上海原PID2784474/start47557208/argv/cwd/fd1/HEAD00e/UUID0，Train1/50 123→131/4686增长，最终独审留档。
- 8旧hold仅核元数据/655声明引用与13授权文件元数据，无新授权或科学复测；GPU1继续让出、M206保持暂停，原goal/协议/禁用项/调度不变。真实收尾report/finish并核释放。

## 5. Decisions Made
- PSNC本次best.5001低于M95.5020，仅归档此实现结果，不重启或整体否定hierarchy。
- BTC仅技术准入并真实训练启动，效果仍UNKNOWN；推理延迟变慢如实保留。已有项目级授权覆盖本次常规操作，无新确认事项。
- 本轮1次真实准入/启动后可收尾，不为凑满额度或reserve计数造变体；后续监测原BTC及自然终态。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
