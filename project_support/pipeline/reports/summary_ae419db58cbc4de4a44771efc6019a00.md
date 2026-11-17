# Research Pipeline Report - cluster_project
快照时间：2026-10-19T16:11:09.919063+00:00；生成报告时快照年龄：1824 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-20 00:11:09
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
================================================== 2026-10-20 00:11 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [不可达]

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1] Best=0.4993 21/50 no_improve=2/10 gpu=0 ? 序列: 0.4899, 0.4930, 0.4993, 0.4984, 0.4921

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
- 储备只计可推进候选及已排队项；另有待人工 4、待资源 1、未分类阻塞 0。
- 非终态候选与排队项合计 5；总上限 8。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 124：complete=27 / rejected=91 / blocked=5 / training=1。
- 否决范围：unclassified=91；实现修订累计 7；收据文件 10（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T16:21:42.298011+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T16:21:42.298011+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T16:21:42.298011+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T16:21:42.298011+00:00 |

## 4. This Tick's Actions
- 本轮2026-10-20 00:11:09上海快照，design；归属和旧调度Disabled已核对，仅一次成功begin，首次审批超时未执行。目标0.5100/历史最佳0.5020/差0.0080；GPU1已有授权，资源/科学约束均未改。
- 本轮监控M204 best约0.4993，21/50、no_improve2/10；相对上轮约0.4944有本实验内的新best，但未超历史M95、未到目标，也不是终态匹配效益。00:22:02原PID1085297原生日志Train21/50的1914至1918/4686增长且mtime新鲜，无近期Traceback；未重启/迁移/改代码。
- bootstrap先登记1个稳定diagnosis候选hierarchy-native-superpoint-relabeling-audit，再执行4个固定TRAIN场景的原生partition_points CPU方法。固定前256个物理行作条件中心，身份和重编号逆变换均一致，改变归属数为0/0/0/0。它不是FPS中心、GPU模型prefix或全层级PASS；CPU准备的超点均值也未证明与GPU scatter逐位一致。
- 查明原生导入绑定：工程Python wrapper加当前安装的二进制扩展，均已哈希冻结；提供的CUDA源码old=0/idxs[0]只有源码级风险见证，未证明当前二进制行为、完整物理共成员变化或mask损伤。另实际调用原始FPS扩展CPU分支一次，返回RuntimeError:CPU not supported；CUDA未初始化，不是模型科学失败。
- 已冻结4场景几何、原始FPS/组合层级/身份及逆置换/簇标签无关共成员测试代码和manifest，语法核对通过；因实际资源占用，本轮0GPU诊断尝试、0原生GPU分区/掩码重放/backward，0新模型/准入/队列项/训练，不把准备或CPU控制称为GPU测试成功。
- 00:22:02上海只读核实：server4GPU0为原M204，19863MiB/17%；GPU1为两项外部计算，15667MiB/97%，项目三锁可用但计算上下文非空，仍不得共享。00:22:12 server3SSH255连接超时，其GPU1占用未知，不当作空闲或已占用。未读取密码、抢卡、reset、停他人进程或改其他项目/调度。
- 原分辨率稳定ID已到复查点：复用原4对固定query协议及旧562场景证据，只增加本次实际占用证据，不重复全场景普查或在占用GPU上再次启动。4个辅助监督ID按到期scope检查仍无优先级恢复证据，仅保留原科学状态并做有界回查，不算本轮4项实验，也不反复索要相同确认。
- 本轮实际产出为1新稳定诊断、4场景原生CPU条件控制、1次原始扩展CPU能力测试、源/二进制及几何协议冻结和资源复查；所有mask效果/训练效益/新颖性仍未知。用量窗口仅本轮begin(2026-10-19T16:11:09Z)至finish收据，排除之前读取/晚到记录/末尾回复；具体用量此处未知，以收据为准，缓存属输入、reasoning属输出，不重复相加、不当账单。本报告保存时finish尚未执行。

## 5. Decisions Made
- 本轮科学状态为有限CPU控制及源码风险证据，不是新机制有效、FPS缺陷已证明或训练准入。保留旧全部严格数值失败，不用新0归属变化覆盖旧full-source置换1e-6失败，不实现canonical-seed单算子修补、调参或改名重开FLE/HDS/routing。
- 两项主线诊断的非GPU准备已完成，下一项实际测试需要原生CUDA；按真实live_external_gpu_occupation保留，复查时间见账本，计时器不等于GPU释放。不称独立路线穷尽/no_information_gain/全局暂停或拖到deadline，不凑第二个变体。
- 待真实合法空闲后，优先原固定query分辨率pair0，再原生重编号几何控制，均用新的当前租约和UUID/上下文/三锁检查。server3只有连接、原生资产与独占资源全面恢复才可替代。M204现有训练自然继续；不自动恢复M201/M204，不需要新的GPU1授权。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
