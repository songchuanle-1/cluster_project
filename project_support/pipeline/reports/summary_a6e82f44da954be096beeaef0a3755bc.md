# Research Pipeline Report - cluster_project
快照时间：2026-10-30T08:07:36.868186+00:00；生成报告时快照年龄：3046 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-30 16:07:36
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
| server-4 | 1 | 未知 | 未知 | 未知 |
- 可用 GPU：未做实时占用确认，不能据此分配。
- 监控摘要（begin 已执行，不再重复探测）：
```text
================================================== 2026-10-30 16:07 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  无训练进程

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 waiting=1 withdrawn=6
    待推: [M206-CGCA] configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml gpu=1
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| 无 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 队列无登记运行；远端进程须另核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
- 活跃 0（运行 0 / 认领 0 / 等待 1）；目标 4；准入预算 2。
- 研究储备 2 / 4；储备准备预算 2，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 6、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 2；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 151：complete=45 / rejected=94 / blocked=10 / validation=2。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 13；收据文件 29（含修订或重试，不代表成功率）。
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
- 接管已 INCOMPLETE 的68d真实持久结果，保留其AOC早停和FCB未知启动退出归档，不补旧finish、不重算旧归档或旧D4九源提升。
- 另存并审查SFC与ELC资源策略兼容操作包，适配当前授权GPU0/1每卡1任务；诊断选卡能力仍仅GPU0，原native、worker、生产九源、YAML和科学协议原件保持。
- 本轮完成SFC与ELC共8个真实原生诊断臂，全部单次terminal rc0；自然TRAIN2、动态common参数配对、原loss整体聚合梯度和真实权重更新均有实际支持，无新增逐map、列、行或轮正性门。
- SFC真实技术准入/精确9A D4→C9提升、GPU1唯一canonical启动，并在ELC追加后原PID3696093/start96568246仍严格TRAIN[1,2916]→[1,2920]；SFC历史源码/回执C9保持，真实全局HEAD18e如实分别记录。
- SFC实际资源为9.762532428G，median比配对M95慢3.5591%、P90慢7.7805%、allocated低0.6172%；ELC为9.758338124G，median慢13.1626%、P90慢11.0377%、allocated低0.5611%。两者原15%内存条件均未触发，未宣称全面加速或准确率提升。
- ELC真实完成原标准证据/精确9A C9→18e提升、技术准入及GPU0唯一canonical启动；原PID3786531/start96685141严格TRAIN[1,156]→[1,162]。两次启动均已实际步增核验，SFC原进程及旧C9依赖源码字节、28用户及34生命周期保护成立。
- 两任务最近严格采样于上海2026-10-30 16:53:45至48；均第1轮，无验证mIoU，不以诊断loss或技术准入代替效果。GPU0 ELC与GPU1 SFC均保持原配置/seed1999/epochs50/maxiters70。

## 5. Decisions Made
- 本轮0新候选、0模型修订；技术检查通过不冒充长期效力、正式训练完成或新颖性证明。冠军仍M95 .5020，目标.5100，Phase1及原seed/data/loss/optimizer/precision/schedule/YAML/bans不变。
- SFC在GPU1的真实运行不自动阻塞ELC的GPU0诊断，也不授权GPU共享、驱逐、重放或旧任务恢复。ELC后续计算和派发仍须真实当前证据、兼容来源、原时间窗、UUID/占用/资产和三锁。
- M206暂停、旧10 holds和已耗尽或失败路线保持；不恢复AOC、FCB、PES、APF、HPC等历史任务，不更改调度。所有共享状态仍由root唯一写。
- 未执行的旧postlaunch文书不覆盖真实ELC状态。本轮当前已确认2项正式运行，准确率未知；原deadline不延长，report/finish仍以接下来实际执行结果为准。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
