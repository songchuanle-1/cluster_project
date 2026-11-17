# Research Pipeline Report - cluster_project
快照时间：2026-10-25T16:10:36.841364+00:00；生成报告时快照年龄：2290 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-26 00:10:36
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
================================================== 2026-10-26 00:10 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bcr] Best=0.4929 15/50 no_improve=1/10 gpu=1 ? 序列: 0.4809, 0.4841, 0.4899, 0.4929, 0.4915
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc] 进程未见 (deathwatch 1/3) — 暂不处置

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
- 研究储备 2 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 5、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 2；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 140：complete=33 / rejected=94 / blocked=9 / training=2 / validation=1 / implementation=1。
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
- preflight初始仍2running/0ready，后精确只读发现BTC原PID已退出、唯一原log earlystop31/best.4914；完整42038211B log本远SHA匹配，canonical finalize_task仅归档M211，保留原receipt/source/launch、BCR/M206。
- GPU0 fresh owner/context/原deadline/UUID/实际idle/三锁/assets通过后，原M95/BFC TRAIN2和资源4臂真实完成terminal/rc0；两原TRAIN输入/common843/04231配对，BFC64n3、多stage、56/60nonpower和4W quadrant原loss有限非零梯度+每步slice更新、原skip/HCG/inst→mask均核。
- 原同口径BFC9.775377484G≤10G（M959.762532428G），参数−262912；median−.2208%、P90+3.2118%更慢如实保留，预测allocated−.1121%，observer-smoke allocated+.00214%，既有15%条件未触发；完整unsupported保持，pureTRAIN/FP32/效能未知。
- 4原请求逐一只读reconcile与status/fullobjects/LinuxSHA吻合，实际checker b8fa/全面独审43af/交叉419f通过；9A已测48fc ff-only推进primary/runtime，原28dirty/untracked bytes/status/index空不变，candidate-only YAML既定路径适配。
- 首派发接口因normalized服务器对象丢UUID-map key在任何intent/transport前拒绝；原错误/zero-intent证据保留。新执行副本仅读取SHA绑定raw map并精确核全UUID，独审后才一次_process_queue/一次Popen，不重启/重放或改科学门。
- M213真实receipt812454，GPU0 PID219369/start56265957 Train1 133→141；GPU1 BCR原1215422/start51717921 Train15 3724→3729，publicruntime48fc但BCR科学source11a/8源/YAML/argv/log保持。M206暂停；2running/0ready。
- 既有CTS原bfab九源保存为隔离4e800060/唯一parent实际已测main48fc，源版本独审通过，primary/runtime/28/index/13账不改；旧原prep及ff7禁用native code/parent null不回写，真实原生/资源/准入仍未做。旧8hold/655声明签名/14授权元数据有界复查无新动作，不读旧正文、不开旧失败或恢复M201/M206。

## 5. Decisions Made
- BTC此实现best.4914低于M95.5020，保留自然终态证据，不冷启/扫参或整体否定hierarchy。BFC通过真实技术门后当轮启动，准确率/新颖性仍未知，原schedule/data/seed/YAML/10G/资源白名单/禁项/调度保持。
- 不新增候选（creation0），推进既有CTS的兼容源版本。下一步新建受审4e8版本绑定原生操作包，未来真实空卡且fresh资源核验后按原7036协议做M95/CTS配对；不能用源版本/静态检查代签native或原地启用旧ff7。
- 本轮1新准入/队列/启动未超预算2；两原在训BFC/BCR受保护，M206继续暂停，无需新的用户许可。完整六段/七段留档后按真实finish收据核验释放，不预签。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
