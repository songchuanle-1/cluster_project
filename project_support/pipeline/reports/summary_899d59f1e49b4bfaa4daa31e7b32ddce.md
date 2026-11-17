# Research Pipeline Report - cluster_project
快照时间：2026-10-20T21:05:34.007527+00:00；生成报告时快照年龄：792 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-21 05:05:33
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
================================================== 2026-10-21 05:05 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  无训练进程

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 withdrawn=6
  server-6: done_earlystop=4
  server-3: waiting=1
    待推: [M205-MDC] configs/Quard/ctf_hcg_csort_mdc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mdc.yaml gpu=?
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| 无 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 队列无登记运行；远端进程须另核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M205-MDC | configs/Quard/ctf_hcg_csort_mdc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mdc.yaml | waiting | - | server-3 |
- 活跃 1（运行 0 / 认领 0 / 等待 1）；目标 5；准入预算 2。
- 研究储备 1 / 5；储备准备预算 2，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 4、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 1；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 131：complete=28 / rejected=94 / blocked=8 / deployment=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 12；收据文件 11（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |

## 4. This Tick's Actions
- 按用户“使用server4 两张卡”核验 pinned主机与GPU0/1 UUID、实时空闲和training/diagnostic/exclusive锁；两卡初始空闲。保留旧运行目录4份配置差异，在同主机新建干净隔离worktree并复用已校验编译组件；仅更新server4运行目录字段，原安全同步/实际源码检查完整通过。旧目录差异哈希最终仍完全一致，没有覆盖旧BPS配置、改门槛或驱逐任务。
- 原M205-MDC从server3纯waiting条目移至server4，在确认无PID/claim后使用canonical门控入口启动GPU0。原生训练步数递增已核验；其已测代码、seed1999、50轮、maxiters70和数据配置未变。
- 本轮新增唯一候选M206-CGCA：粗层内容生成分组跨通道关系，再作用于fine自身values，通过原HCG更新inst_feats。独立九文件/YAML，新增0参数且有新非对角信息流；真实TRAIN2次loss/backward/optimizer通过，618观测梯度有限，模块fine/coarse输入边和输出均有限非零，原fine/coarseFFN已更新。
- CGCA同样本原fvcore9.764703308G；同GPU1 bs1/warmup20/repeat100配对median88.503ms/P90100.298ms，M95为86.694/99.900ms，推理峰值显存一致。与M95相同实际训练批次的2步优化器峰值比例1.000338784。M205同时在GPU0训练，共享主机竞争须注明，不能与前轮空载延迟横比。未支持算子留档，没有视为零成本。
- M206四门准入、版本同步、入队及canonical派发全部完成并在GPU1确认原生步数递增。截至05:16:21上海时间：M205 GPU0为第1/50轮1477/4686步；M206 GPU1为第1/50轮53/4686步，两项登记和实际进程/日志一致。尚无新验证mIoU。
- 首次收尾因两条complete历史记录直接引用已变动的SERVERS.yaml而拒绝。现将引用位置冻结到变动前已留存的同字节快照，SHA仍为原60cba26a，历史结果、其它字段及修订记录完全不变；保留修复前记录与迁移审计，没有修改校验器或把索引维护计作研究成果。

## 5. Decisions Made
- 本轮完成server4双卡各一个独立单卡实验，没有复制实验、改双卡DDP训练或更改数据/seed/epoch/LR。新候选1项，8项旧挂起和全部失败/修订上限保留。既有项目授权覆盖例行保存版本、同步、入队和训练，无需再次索要常规审批。
- 保留所有诊断失败：一次基线显存检查因本轮资源进程尚占GPU1，被运行时在CUDA前正确拒绝；顺序等待后独立不可变重试成功。不是模型训练失败，未共享或清锁。
- 两项正式训练已核实启动，工程准入不等于有效性。历史最佳mIoU0.5020、目标0.5100、差0.0080不变；下一步按既有监控与patience观察验证结果，不提前宣称收益或新增调整。调度、科学阈值、资源白名单未变。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
