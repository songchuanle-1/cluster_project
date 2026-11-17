# Research Pipeline Report - cluster_project
快照时间：2026-10-19T20:09:18.413082+00:00；生成报告时快照年龄：1763 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-20 04:09:17
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
================================================== 2026-10-20 04:09 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [不可达]

--- server-4 (192.168.1.115) ---
  无训练进程
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1] 进程未见 (deathwatch 1/3) — 暂不处置

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
- 本轮2026-10-20 04:09:18上海design快照；真实归属/前台模式/旧调度Disabled及当前目标授权已核对，仅一次begin。快照登记M204运行但进程未见(deathwatch1/3)，不将登记当作训练。历史最佳M95为0.5020、目标0.5100、差0.0080，仍未达标。
- 04:12:24严格身份/UUID和实时三锁核实：M204原PID已消失，原生日志04:06:30结束并明确第28/50轮patience10早停。GPU0为41MiB/0%、无计算上下文且三锁可用；GPU1另有一项外部计算，9673MiB/77%；04:12:33 server3密钥SSH255超时，其GPU1占用未知。未抢卡、reset、迁移、恢复M201/M204或改队列消失计数。
- 最先读取的20261019_093003/best及last仍是保留的第5轮恢复输入，已留证但不作本次最终指标。随后沿原生日志真实保存标记定位20261019_162904：best为第18轮，原生标量记录0.49925217；last为第27轮/未提升9次，原生第28轮break在保存之前。真实best未超M95；不把自然早停或本次核验当新训练/准入。队列终态仍待规范后续监控归档，未强制改记录。
- 两项到期主线先恢复原稳定ID验证：预先冻结纯GPU0资源映射，仅改卡号/UUID/锁路径及清单位置；反向替换能恢复原运行器，原模型/config/checkpoint/样本/seed1999/协议与1e-6阈值均不变。每项执行前仍检查实际空闲、资产哈希、当前执行租约和三锁独占。
- 原分辨率pair0实际原生前向：4表达支持667、4表达支持255，原细层为255token。point/features/mask/score/identity控制均0，重新聚合误差1.9073486328125e-6超过原1e-6，原断言在干预前停止。mask干预完成0对，余下原3对未运行，不算失败/完成，也不据此否定分辨率耦合假设。
- 原生FPS/组合层级重标号几何测试真实完成4固定TRAIN场景，12/12层身份重放通过、12/12层物理共成员改变；当前二进制首物理种子0在逆序后对应666/709/2328/405。它证明这组样本的几何行序敏感性，不证明有害缺陷、新颖性、修复收益或源码与二进制全对应。
- 在结果之后、执行之前预注册同ID的固定query mask扩展：2对/4场景/16表达，保留原生prefix/query/targets，只以原FPS重算重编号层级。两对都完成；其余五项原生重放控制为0，但重聚合均1.907e-6，仍不通过原1e-6。原始点message最大变化1.5078/1.58795，mask最大变化9.5246/11.1023仅为受限原始读数，任务因果收益/伤害未定；实际匹配query行数、表达覆盖和逐场景均值见analysis.json，不把相关行当独立样本。
- 仅CPU绑定核验当前模型确用scatter_mean；实际安装源码说明GPU原子归约非确定性，与误差相容但未隔离成因。未重复内核试到PASS、改精度、换seed、放宽阈值或改原模型。四个诊断进程均退出后释放；最终GPU0无计算上下文且三锁可用，有独立释放证据。因此当前主线改记真实numerical_control_failure，而非继续谎报资源或授权阻塞。
- 实际产出为4个原生GPU诊断进程(1分辨率控制失败、1几何4场景、2固定query mask对)，2次只读checkpoint元信息核验、1次安装源码绑定及释放检查；0新候选/模型/backward/准入/队列项/训练。原有CPU562场景普查和旧数值失败全部复用保留。辅助监督只在实际到期时作范围复查，不新增优先级或反复索要授权。
- 用量只覆盖本轮begin(2026-10-19T20:09:18Z)至finish收据前可见本地记录，排除此前读取、晚到记录和最终回复；此处具体用量未知，以收据为准。缓存已在输入、reasoning已在输出，不重复相加、不视为账单。完整六段复用快照事实表，后续变化在本节注明；保存时finish尚未执行。

## 5. Decisions Made
- 本轮科学结论分开：M204该次训练未超过历史最佳；4场景原生几何行序敏感性已观察到；重标号对mask的收益/伤害仍因严格数值控制失败而未定。后者不是模型有效或假设被科学证伪，不改成PASS，不自动开启训练。
- 两项不同干预的有限原生测试共享一项真实失败的测量前提，源码审计尚未建立具体可证明修复；对继续相同重放设置有证据的短期no_information_gain冷却。该名称仅指进一步不变重放无新增诊断力，不抹去本轮新观察、不称全局路线穷尽/独立科学否定/资源不足或截止已到。原3个未运行分辨率对仍保持未执行。
- 恢复条件为同稳定ID下出现具体、预注册且能守住原1e-6控制的测量实现证据；当前无已证明的修复，不靠计时器授权复跑/改阈值或制造变体。GPU0空闲不等于候选准入；保留M204全部输入/输出及native早停状态，后续由规范监控归档，不重启/迁移。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
