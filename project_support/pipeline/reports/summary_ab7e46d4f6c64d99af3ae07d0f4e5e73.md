# Research Pipeline Report - cluster_project
快照时间：2026-10-25T04:06:01.065273+00:00；生成报告时快照年龄：1601 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-25 12:06:00
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
================================================== 2026-10-25 12:05 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc] Best=0.4908 18/50 no_improve=1/10 gpu=0 ? 序列: 0.4852, 0.4894, 0.4890, 0.4908, 0.4889
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bcr] 1/50 尚无验证 - gpu=1

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 running=2 waiting=1 withdrawn=6
    待推: [M206-CGCA] configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml gpu=1
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M211-BTC | configs/Quard/ctf_hcg_csort_btc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |
| M212-BCR | configs/Quard/ctf_hcg_csort_bcr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bcr.yaml | server-4 | 1 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
- 活跃 2（运行 2 / 认领 0 / 等待 1）；目标 4；准入预算 2。
- 研究储备 0 / 2；储备准备预算 2，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 5、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 0；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 138：complete=33 / rejected=94 / blocked=9 / training=2。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 12；收据文件 18（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| hierarchy-coarse-conditioned-fine-channel-attention | Preserve manually paused M206 and full epoch24 checkpoint. Do not resume/migrate/cold-start on any GPU without a later explicit human instruction; GPU1 remains released to others. | 2026-10-22T16:24:16.243554+00:00 |

## 4. This Tick's Actions
- 本轮快照2running/0ready，due0、旧9parked未到期。实际原PID/start/argv/cwd/fd1/source8/YAML/UUID/HEAD11a观察：BTC GPU0 Train18/50 921→926，BCR GPU1 Train1/50 978→984；两任务健康，无新终态。
- 实现单一新结构M213-BFC：同原parent内多阶段同步双输出butterfly，保留n个C状态，原LN/cfskip/fine-coarse/rawCSORT/FPS/HCG/单inst不变；原字节YAML不改。
- 实际作者197963 stdlib断言/152有效plan/13拒绝及独立生产plan+forward列表替身n0..128/22特殊/16非法/源集成核通过；数目为检查非训练实验，抽象cap128非原native64。首harness方法名笔误保留，未改模型或门。
- 在独审后只将9已核字节保存为isolated48fc单父11a；主仓/公共runtime11a、原28status+bytes/index及11账保持。sourceprep8512原commitnull不回写，版本证明独立留档。
- 禁用BFC native包14map/12diag及14作者本地检查/7包核、46项独审完成；DRAFTTrue、10activefieldsnull，无lease/binding/adapter/native或资源执行。额外同call双half非零harness门按已冻结协议修正并留旧版，四W象限门不变。
- M213以source准备储备登记validation，native/资源/效能NOT_RUN，未来等待空卡/fresh guard后原TRAIN2和资源配对；本轮0准入/0新queue/0新GPU计算/0live源码变更/0launch，原BTC0/BCR1与M206暂停保持。

## 5. Decisions Made
- 复用standing2e892及GPU0/1 grant90f，现有2任务不挤占；M206和旧9parked不因资源开放重开。M213是新图备选，不宣称novelty/可逆/无损/selfexclusive或有效性。
- 源推断新262656参数、差−262912、每middlelinear最多+58.720M MAC；示例总9.821253G仅估计而非资源PASS，真实原10G/延迟/显存/unsupported配对仍待测。
- 本轮一个真实implementation_test和可复核准备结果已完成，按experiment-first规则收尾；不为凑足2个候选而继续造备选。原deadline不延长，不修改scheduler、资源边界、源YAML/seed/schedule/data或任何历史控制。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
