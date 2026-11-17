# Research Pipeline Report - cluster_project
快照时间：2026-10-22T22:12:37.878024+00:00；生成报告时快照年龄：233 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-23 06:12:37
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
================================================== 2026-10-23 06:12 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hrc] Best=0.4883 17/50 no_improve=0/10 gpu=0 ? 序列: 0.4763, 0.4854, 0.4842, 0.4855, 0.4883

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 running=1 waiting=2 withdrawn=6
    待推: [M206-CGCA] configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml gpu=1
    待推: [M209-PSBR] configs/Quard/ctf_hcg_csort_psbr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psbr.yaml gpu=0
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M208-HRC | configs/Quard/ctf_hcg_csort_hrc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hrc.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
| 2 | M209-PSBR | configs/Quard/ctf_hcg_csort_psbr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psbr.yaml | waiting | - | server-4 |
- 活跃 2（运行 1 / 认领 0 / 等待 2）；目标 3；准入预算 1。
- 研究储备 1 / 2；储备准备预算 1，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 5、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 1；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 136：complete=30 / rejected=94 / blocked=10 / training=1 / deployment=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 12；收据文件 15（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| hierarchy-coarse-conditioned-fine-channel-attention | Preserve manually paused M206 and full epoch24 checkpoint. Do not resume/migrate/cold-start on any GPU without a later explicit human instruction; GPU1 remains released to others. | 2026-10-22T16:24:16.243554+00:00 |

## 4. This Tick's Actions
- 实际会话与foreground target一致，已读canonical SKILL/experimentfirst/foreground/最新memory与goal/SERVERS；goalSHA0441、server4GPU0 max1/GPU1释放/M206暂停/WindowsDisabled保持。前42ce FINALIZED released且无headless lock/pending；原generated22:12:37.878024UTC/deadline23:12:37.878024不改。
- begin先monitor/派发已有合格队列/goal一次，operationalissues空、新终态0；1running/0claiming/1readyPSBRwaiting，M206人工paused另计。已有PSBR排队和PSNC完整具体准备，未为候选预算1重复设计或准备工具。
- 2026-10-23 06:13:09上海额外只读核HRC原PID2780804/start29604100/原argv/cwd/HEAD74f/UUID，native17/50步485→495/4686，无error、logfresh/GPU0仅原HRC context。begin06:12partial best.4883/noimprove0，非最终效果/新champion。GPU1未查询/使用，无signal/新计算。
- 资源仍busy，PSNC仅做当前resource_check blocked；沿用已有source43/完整operationalpacket/静态release。未重跑51mock/guard/旧native或改9源字节，不假造原生PASS。PSBR等待74f/nohold/PIDnull且receiptJSONhash未变；标准artifact正文沿用前42ce验证，不冒称本轮重检。主74f/index空，三个静态metadata/release anchor吻合。
- 到期8旧hold仅核完整canonical元数据和声明path/hash清单签名、13授权path-size-mtime，无变化；不读/hash/stat655证据正文、不重读grant正文、不重开/增加修订/重复人类问题。M206原paused/GPU1释放保持。
- 只读辅助reader首用legacy缺experiment_id记录出现KeyError，改为get后完成；失败发生在写artifact前，无模型、协议阈值、台账变更，修复范围如waiting_boundary_check.json所列。
- 当前tick_attempt真实resource_check blocked证据同归PSNC；仅更新小范围候选当前资源事实/证据和七段memory。0新候选/native/资源profile/标准summary/receipt/queue/launch/Gitcommit/sync，既有queue/running/experiment/receipt字节保持。没有新科学结论、完成、失败或需处理事项，本轮DONT_NOTIFY。
- 脚本生成完整六段报告后按原token真实finish与receipt/lease释放核验，不预写PASS、不在释放后回写。不写重复decision日志，不建全局穷尽/冷却，不改调度/资源/目标/原失败；下一步仍是等待GPU0与PSBR版本边界安全后用现成工具/freshbinding做真实原YAML TRAIN2+原资源。

## 5. Decisions Made
- 延续既有授权、FIFO与资源等待；无新路线或操作决策，不生成重复decision日志。健康训练/等待状态未变且无可行动事项，静默。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
