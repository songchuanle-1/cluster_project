# Research Pipeline Report - cluster_project
快照时间：2026-10-22T02:12:05.347438+00:00；生成报告时快照年龄：2224 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-22 10:12:04
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
================================================== 2026-10-22 10:11 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca] Best=0.4953 24/50 no_improve=6/10 gpu=1 ? 序列: 0.4902, 0.4909, 0.4899, 0.4868, 0.4869
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap] Best=0.4919 16/50 no_improve=0/10 gpu=0 ? 序列: 0.4813, 0.4897, 0.4887, 0.4880, 0.4919

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 running=2 withdrawn=6
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | server-4 | 1 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |
| M207-HAP | configs/Quard/ctf_hcg_csort_hap/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 2（运行 2 / 认领 0 / 等待 0）；目标 4；准入预算 2。
- 研究储备 0 / 2；储备准备预算 2，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 4、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 0；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 134：complete=29 / rejected=94 / blocked=9 / training=2。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 12；收据文件 13（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |

## 4. This Tick's Actions
- 10:13:14与新PSBR静态准备后10:35:12上海时间两次有界资源核：server4 strict known-host/pinned hostname/物理UUID匹配，原PID/starttime/argv/cwd及native日志步增；最新GPU0 HAP17/50 2011→2012、GPU1 CGCA原full-resume24/50 3937→3938，各仅原context，max1任务/卡，无可用空槽。未更动任何现有/外部训练。10:12监控缓存Best为HAP.4919/CGCA.4953，不把当前epoch或三位小数尾日志当最佳发生epoch/新精确Best。
- 新增M209-PSBR单一独立结构：保留原FPS/IDs/rawbanks/CSORT/fine-coarse FFN/LN/HCG及单末层inst更新；middle在原coarse父组内按detached原centroid xyz+ID固定序，共享Wx/Wh双向tanh状态经concat Wo输出，移除整个旧middle residual FFN。真实support=ids1[ids0]，空ID/padding不进入状态、结果逆散回原ID，每父组/batch/方向边界零状态。未改YAML数值/seed1999/50epochs/maxiters70，原生检查与效果仍未测。
- 作者50项源/AST/compile/原YAML一致性检查、独立24项静态核与约束审均无确定阻断；已仅9个新增模型源/配置文件本地提交74fcd21df，parent9e543af。原28脏/未跟踪文件字节和status保持、index空，HRC9源和所有已冻结包未改；无push/sync/远端HEAD切换。
- PSBR专属native worker/template/runtime已冻结：48项静态与独立14项检查；新Wx/Wh/Wo真实native梯度/更新、非单例组、原loss.backward、HCG/CSORT/inst→ILA→mask路径及两批/共同参数fingerprint均为未来执行观测，当前NOT_RUN。原resources函数及7runtime函数AST保持；没有torch/SSH/GPU/activelease执行。
- PSBR执行adapter仅从已测HRC程序替换候选常量/路径，完整文本/AST差异受限；31离线mock和34静态检查通过，来源/安全/结果边界独立复核。root先将精确prep/release/source外锚入候选，再实际本地guard/prepare集成：当前owner/context/授权通过，GPU0/1均因登记原任务在transport前拒绝；0transport、无生产binding/manifest/lease/staging。
- 8个到期旧hold有界复核：摘要中的stage/blocker/revision保持、655直接引用hash匹配，无新的解封/追加修订授权。PCE3次/RSTR2次额度耗尽及旧失败、4监督辅助scope/2测量实现hold保持；不把到期当解除权限。保存7段memory、next_batch决策和本轮真实resource_check/blocked证据。

## 5. Decisions Made
- 选PSBR为一个真实新计算图假设，不为额度凑数：其跨middle sibling的非线性共享状态边不同于MDC一跳方向卷积、HRC逐层mean组合、HAP仿射传播或CGCA coarse Gram。有限源/历史索引核查未见直接重开禁用，不宣称文献/全史新颖性或已证任务瓶颈。新middle262656对旧525568参数只是静态算术，serial延迟/全部资源与效益UNKNOWN。
- 保留原构造序，只有新增recurrence构造使用CPU fork_rng(devices=[])恢复后续随机数位置，不manual_seed、改默认init或做初始化搜索；随机序列重用相关性已披露，实际共同参数/两批loader配对不能用静态控制代签。
- HRC与PSBR保持blocked/exclusive_gpu_slot/resumevalidation，实证retry为UTC03:35:12.090022或真实队列空槽事件，不延长本轮原UTC03:12:05.347438 deadline。先推进已准备HRC，再PSBR；有实际授权空槽后各用当前root新binding/manifest/lease/独立stage，保留原运行。
- 所有新native/资源仍NOT_RUN。适配器四个raw completed结果不是准入；真实loss/backward/参数更新/新路径、共同初始化与两批指纹、原资源协议与unsupported/内存范围核后，另生成真实标准smoke/资源汇总，closure准入后才原YAML入队并当轮canonical派发。offdiagonal/reset-state诊断未实现未测；smoke含observer内存，纯TRAIN峰值UNKNOWN支持项，不新加门槛。超时只精确reconcile旧stage/request/PID/startticks/argv/result，不续租/重放/kill/删证据。
- 本轮1新候选/0模型修订/1仅本地9文件提交/0同步/0准入/0入队/0启动/0终态，standing项目授权已覆盖，无新用户审批。新独立变体及原生执行准备是本轮通知理由；例行在训进度本身不是新科学结论。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
