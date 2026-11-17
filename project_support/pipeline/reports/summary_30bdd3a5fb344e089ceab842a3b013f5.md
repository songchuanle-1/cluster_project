# Research Pipeline Report - cluster_project
快照时间：2026-10-19T13:37:42.375992+00:00；生成报告时快照年龄：2593 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-19 21:37:41
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
- 可用 GPU：未做实时占用确认，不能据此分配。
- 监控摘要（begin 已执行，不再重复探测）：
```text
================================================== 2026-10-19 21:37 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [不可达]

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1] Best=0.4944 16/50 no_improve=3/10 gpu=0 ? 序列: 0.4803, 0.4944, 0.4930, 0.4874, 0.4899

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
- 活跃 1（运行 1 / 认领 0 / 等待 0）；目标 2；准入预算 1。
- 本次执行故障（不等于缺候选或缺授权）：
| 服务器 | 实验 | 故障 |
|---|---|---|
| server-3 | 未知 | 服务器不可达，实时进程与资源未知 |
- 研究储备 0 / 2；储备准备预算 2，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 4、待资源 2、未分类阻塞 0。
- 非终态候选与排队项合计 6；总上限 8。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 123：complete=25 / rejected=91 / blocked=6 / training=1。
- 否决范围：unclassified=91；实现修订累计 5；收据文件 10（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T16:21:42.298011+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T16:21:42.298011+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T16:21:42.298011+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T16:21:42.298011+00:00 |

## 4. This Tick's Actions
- 收到本会话明确人工授权“授权GPU1 可以做实验”后，在当前前台租约内将server4 allowed_gpus改为[0,1]，追加固定UUID及goal资源约束/授权留档；保留server3GPU1、GPU0上的M204和全部科学约束。资源更新发生在begin之后，旧快照不重写、不重复preflight；更新后总名义容量3，不把新增卡授权当科学准入例外。
- 重新实测GPU1 UUID/空闲/三独占锁，独立运行目录仅改物理GPU编号、UUID和锁名；模型、配置、checkpoint、seed1999、epochs50/max_iters70、原8场景32表达及1e-6阈值不变。原生运行按卡独占、逐对串行，未复制大型checkpoint或干扰GPU0。
- 保留2次原始失败：尺度完整源置换误差2.86102294921875e-6未过1e-6；表达读数遇bool减法错误。先预登记两项测量层修正，再运行：原标签等值dtype转换；置换控制固定原融合logits并增加identity。完整源置换失败单独保留，不冒称原完整源置换PASS，不改实际baseline/尺度删除或模型。
- 两组修正后各4对场景全部实际执行。表达固定query消息移植7/8场景误差升高，场景等权均值+0.004466350；尺度细/粗混合fine-cell预期正向只2/8，均值-0.006994256，30/32表达可读。两组匹配原生控制最大误差0，原1e-6不放宽；保留全部反向/空分组，不把295相关query行当独立样本或编造总体区间。
- 22:08:54上海核实GPU1计算进程为空、三锁全释放；GPU0仍为原M204 PID1085297，Train[17/50]2947→2952/4686且日志新鲜，无重启/迁移。begin的best约0.4944@16/50是21:37快照，非本轮诊断收益；server3预检报告不可达，未重探/修复或沿用旧健康说法。
- 实际产出为2个有界原生诊断、10次原生尝试（2次原失败+8对修正后运行）、2次预登记测量修正、GPU1授权和清理证据；0新模型/准入/新训练。源码派发器旧版已按原hash归档并仅迁移源码证据路径，负结果不改。用量为begin至receipt本地部分窗口，当前完整收据待生成；cache/input和reasoning/output不重复叠加，也不是账单。

## 5. Decisions Made
- 两个原稳定ID仅完成预注册的固定TRAIN cohort诊断，科学状态仍为条件性机制读数/总体与新机制效益未知，不是全模型效果或训练mIoU提升。表达特异点侧信息得到该固定样本方向支持；“细尺度相对更负责边界”预期未获本组支持，不能为故事忽略反例。
- GPU1已获资源授权且本轮真实执行完毕，之后仍按同一白名单/新鲜占用/独占锁/冻结资产/科学准入执行实验，无需重复索取同一GPU1授权。GPU0 M204继续原训练，不新增未经准入的长训练，不改scheduler或其他项目。
- 遗留未完成项只剩4个原辅助scope hold；机器stop_reason的external_resource_blocked在此仅指它们，绝不表示GPU1仍被阻塞、全项目暂停、准备预算为0或所有独立路线耗尽。本次明确用户资源操作及两组有界预注册诊断已完成，不凑同义变体填空卡。
- 本报告保存时finish待验证；只有finish显式通过、收据FINALIZED及上下文提交/所属租约和待提交状态释放均核实后才称本轮完成。所有原始失败、1e-6及历史科学门槛保留，释放后不补写项目。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
