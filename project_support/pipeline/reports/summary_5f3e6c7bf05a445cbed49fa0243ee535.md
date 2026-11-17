# Research Pipeline Report - cluster_project
快照时间：2026-10-29T14:04:06.172709+00:00；生成报告时快照年龄：1804 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-29 22:04:05
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
================================================== 2026-10-29 22:04 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  无训练进程
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pes] 进程未见 (deathwatch 1/3) — 暂不处置

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
| M221-PES | configs/Quard/ctf_hcg_csort_pes/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pes.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
- 活跃 1（运行 1 / 认领 0 / 等待 1）；目标 3；准入预算 2。
- 研究储备 1 / 2；储备准备预算 1，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 6、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 1；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 149：complete=42 / rejected=94 / blocked=11 / training=1 / validation=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 13；收据文件 27（含修订或重试，不代表成功率）。
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
- 原PES在第5/50轮529/4686因参数迭代ValueError异常退出，4次验证partial best0.4211066663265228。完整原日志/原PID消失/8源及YAML/精确指标经独审后canonical一次crashed归档；原因UNKNOWN/inconclusive，不自动恢复或当正常早停。
- GPU0真实空闲且三锁可用、canonical旧槽清理后，原AOC9cf/e45执行fresh prepare-stage和四实际臂；两自然TRAIN/common初始化匹配、sharedcell两stage/q两directmean/wholecell原loss梯度与真实更新及原HCG单inst路径通过独审。
- AOC同口径资源9.724783692G，median/P90比对照慢约1.99%/4.29%，allocated约低0.617%，15%显存条件未触发；fullunsupported与原测试口径保留，训练收益/纯TRAIN峰值未知。
- 真实actualpeer绑定新副本后，仅exact9A ff与safe sync0314、真实receipt bf4426准入一次，再canonical GPU0派发一次。原AOC3437349/start90046755在上海22:26:42至45首轮156→165/4686，未输出验证值。
- FCB当前实际AOC0314父与技术receipt已就绪，本地guard passes且transport0；GPU0被原AOC占用，freshcanonical查询核忙，FCB原生继续等待。GPU1不使用，旧任务/暂停/失败和用户28文件/index保持。

## 5. Decisions Made
- 最佳仍M95 .5020、目标.5100；PES为未完成训练的异常结果，不能作效果/机制否定；AOC只有真实技术准入与正式步增，尚无验证效果。
- 保留PES原source9c/receipt6fce/技术证据与checkpoint，不因队列容量或本轮heartbeat自动恢复。PES具体运行时原因未知，AOC后续成功不等于修复旧异常。
- 监控唯一原AOC GPU0任务，不重放旧progress_pending；FCB仅在卡自然释放且fresh owner/原deadline/source/UUID/assets/三锁复核后跑原d4 pairedTRAIN2/resources，过了再准入。
- 本轮无新模型/新commit，不动goal/bans/资源/数据/seed/schedule/旧授权或调度。新真实基线是0314/28账，后续接管须更新SOURCE和观察器；无需用户重复授权普通项目操作。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
