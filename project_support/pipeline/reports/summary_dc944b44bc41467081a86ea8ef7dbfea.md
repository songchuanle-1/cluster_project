# Research Pipeline Report - cluster_project
快照时间：2026-10-19T18:13:48.142346+00:00；生成报告时快照年龄：506 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-20 02:13:47
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
| server-3 | 1 | 未知 | 未知 | 未知 |
| server-4 | 0 | 未知 | 未知 | 未知 |
| server-4 | 1 | 未知 | 未知 | 未知 |
- 可用 GPU：未做实时占用确认，不能据此分配。
- 监控摘要（begin 已执行，不再重复探测）：
```text
================================================== 2026-10-20 02:13 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [不可达]

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1] Best=0.4993 25/50 no_improve=6/10 gpu=0 ? 序列: 0.4921, 0.4949, 0.4889, 0.4854, 0.4913

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 running=1 withdrawn=6
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M204-CPA | configs/Quard/ctf_hcg_csort_cpa_r1/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 1（运行 1 / 认领 0 / 等待 0）；目标 3；准入预算 2。
- 本次执行故障（不等于缺候选或缺授权）：
| 服务器 | 实验 | 故障 |
|---|---|---|
| server-3 | 未知 | 服务器不可达，实时进程与资源未知 |
- 研究储备 0 / 2；储备准备预算 2，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 4、待资源 2、未分类阻塞 0。
- 非终态候选与排队项合计 6；总上限 8。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 125：complete=27 / rejected=91 / blocked=6 / training=1。
- 否决范围：unclassified=91；实现修订累计 7；收据文件 10（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T20:37:50.316851+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T20:37:50.316851+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T20:37:50.316851+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T20:37:50.316851+00:00 |

## 4. This Tick's Actions
- 本轮快照2026-10-20 02:13:48上海，design；已核对真实所属任务、前台模式及旧调度Disabled，仅执行一次begin。目标0.5100、历史最佳M95为0.5020、差0.0080；GPU1原授权有效，未更改科学或资源规则。
- 预检监控M204-CPA最佳约0.4993、25/50、连续6/10次未刷新；最佳与前轮相同，未超过M95或目标。02:18:40原PID1085297原生日志Train25/50步数1519至1523/4686持续增长、mtime新鲜且无近期Traceback；不是仅凭登记或PID判断训练。精确当前全精度指标未知，未重启或迁移。
- 02:18:40上海严格主机身份和授权UUID检查通过：server4GPU0为原M204、19863MiB/28%、三锁占用；GPU1为两项外部计算、16065MiB/100%，三项项目锁虽可用，仍不得共享。server3本轮有界密钥SSH主机查询超时，GPU1占用未知，不当作空闲或占用；未读取密码、抢卡、reset或处置外部进程。
- 按ID续做hierarchy-native-batch-minimum-resolution和hierarchy-native-superpoint-relabeling-audit的到期资源检查，验证保留证据哈希，并追加本次真实占用证据。前者保持原4对/32表达固定query与严格1e-6控制、从pair0恢复；后者保持原生FPS/组合层级/身份逆置换及物理共成员控制。均未准入，资源计时器不代表可执行。
- 复用已完成的562场景普查、4场景CPU固定中心控制及CPU不支持原始FPS的旧证据，未重复计算或把它们计作本轮实验。四个辅助监督候选未到复查点，保留原优先级和科学状态；未重新索要授权、恢复M201或制造同类变体。
- 本轮实际产出为两项到期候选的资源证据更新、两张授权server4卡的实时占用核验、一次server3连接检查及M204原生进度确认；0新增科学CPU/GPU诊断、0mask对、0backward、0新模型/准入/入队/训练。一次本地SSH命令构造失败已保留并修正，未算远端故障或科学失败。
- 用量窗口仅本轮begin(2026-10-19T18:13:48Z)至finish收据的本地记录，排除此前读取、晚到记录和最终回复；当前具体用量未知，以收据为准。缓存包含在输入、reasoning包含在输出，不重复相加、不视为账单。完整六段复用脚本事实表；本报告保存时finish尚未执行。

## 5. Decisions Made
- 科学状态仍为证据不足/等待实际原生CUDA测试，没有新的机制收益或损害结论。严格保留旧full-source置换等数值失败，不放宽阈值、不修改冻结样本/query/目标/seed/schedule/FLOPs，也不把资源复查当新创新。
- 两项主线的非GPU准备已完成，当前下一项需要原生CUDA；按真实外部占用及server3不可达保留有界资源阻塞，不声称独立路线穷尽、无信息增益或截止已到。未发现有证据支撑的独立可执行非GPU测试，不为填预算制造候选。
- 实际授权GPU1释放并通过新当前租约、UUID/上下文/空闲、原生资产/runtime与三锁检查后，先续原分辨率pair0，再续原生重标号几何控制。server3仅在身份/连接/原生资产/独占条件完整恢复后使用；M204自然继续，不自动重启/迁移/驱逐，不需要新的GPU1授权。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
