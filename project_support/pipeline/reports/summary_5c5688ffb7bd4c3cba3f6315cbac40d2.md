# Research Pipeline Report - cluster_project
快照时间：2026-10-20T23:11:05.142462+00:00；生成报告时快照年龄：304 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-21 07:11:04
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
================================================== 2026-10-21 07:10 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mdc] Best=0.4023 4/50 no_improve=0/10 gpu=0 ? 序列: 0.3042, 0.3795, 0.4023
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca] Best=0.3808 3/50 no_improve=0/10 gpu=1 ? 序列: 0.2762, 0.3808

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
| M205-MDC | configs/Quard/ctf_hcg_csort_mdc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mdc.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |
| M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | server-4 | 1 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 2（运行 2 / 认领 0 / 等待 0）；目标 5；准入预算 2。
- 研究储备 1 / 3；储备准备预算 2，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 4、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 1；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 133：complete=28 / rejected=94 / blocked=8 / training=2 / validation=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 12；收据文件 12（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |

## 4. This Tick's Actions
- 上海2026-10-21 07:10 begin已完成进展/目标检查及已有合格队列派发检查，waiting0，无终态/运维问题；M205-MDC Best=.4023、第4/50轮，M206-CGCA Best=.3808、第3/50轮，均no_improve0/10。与前轮相比继续增长，但最终收益仍待训练。
- 07:12:04严格已知主机/hostname/两卡UUID/contexts核验，server4 GPU0 PID3842306、GPU1 PID3873690仍占用；没有共享或改动运行中的任务。
- 继续已有M207-HAP：核对本地8源+1YAML逐字节等于f51823bb提交；原YAML和M95字节相同。只读校验实际基线源码/训练入口/数据集源码/annotation/backbone pretrain及frozen M95 checksum，未加载checkpoint为模型或创建tensor。
- 在新私有目录hap_5c5688ff组装13文件完整检查包，包括fresh runtime/manifest/当前租约/原worker/8源/YAML。远端AST/compile和所有payload hash核验完成；既有训练代码根没有修改。
- 独立只读复核确认GPU0/UUID0/query/lock/env和token/thread/deadline/manifestSHA一致，acquire在torch之前；修正了旧CGCA元数据GPU0与实际runtimeGPU1不一致的复制风险。旧文件原字节保留。
- 实际执行同一native_runtime.acquire的受限probe：因GPU0占用在torch/gorilla/worker/setup前拒绝，before/after CUDA contexts一致，无自身CUDA context，0forward/0optimizer、持有锁0。即使意外空卡probe也只释放自身锁停止；没有执行原生smoke。
- 新resource_check/blocked、完整检查包与guard证据绑定当前HAP/tick_attempt；0新候选、0模型源代码提交、0原生数据/backward/资源计算、0准入/入队/启动。

## 5. Decisions Made
- 保留两项现有正式训练和原验证/早停协议，不按当前早期mIoU判断最终收益，不驱逐任务或以低util/旧flock可用推断空闲。
- HAP保持validation/native_status=pending_resource。真实空闲server4卡出现后，用新foreground token、原deadline、同一精确版本/原YAML/资产重建私有stage并重验UUID/contexts/locks，再执行TRAIN两步和配对资源，实测PASS才准入/安全同步/派发。旧stage和lease不可跨tick直接重放。
- 本轮guard成功拒绝只是资源前置检查结果，不是HAP数值/梯度/FLOPs/延迟/显存或准确率PASS。pinv observer的既有诊断局限继续保留并分开归因。
- 复用已有项目操作授权；无新增用户决定事项，不更改目标/资源边界/禁用项/调度/历史冻结结果，不凑新增候选配额。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
