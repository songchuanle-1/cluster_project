# Research Pipeline Report - cluster_project
快照时间：2026-10-19T08:48:39.715349+00:00；生成报告时快照年龄：3085 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-19 16:48:39
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
================================================== 2026-10-19 16:48 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1] 6/50 尚无验证 - gpu=0

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
- 研究储备 0 / 2；储备准备预算 2，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 4、待资源 0、未分类阻塞 0。
- 非终态候选与排队项合计 4；总上限 8。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 121：complete=25 / rejected=91 / blocked=4 / training=1。
- 否决范围：unclassified=91；实现修订累计 5；收据文件 10（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T10:39:42.055835+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T10:39:42.055835+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T10:39:42.055835+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T10:39:42.055835+00:00 |

## 4. This Tick's Actions
- 本轮快照16:48:39上海；在本轮租约内创建1个点特征层级责任诊断，并先做原生源合成CPU契约。重建/query独立性/padding误差0，但float32置换1.0728836059570312e-6未过原1e-6；保留原失败。
- 事前登记同fixture提升float64精度鉴别：置换误差0。另实际回放真实M95两场景8表达缓存：float32源重建/置换3.814697265625e-6、删除代数最大2.4318695068359375e-5，均未过；float64内部置换0、代数误差约4.44e-14，但对GPU缓存仍7.48e-6未过。不覆盖任何原失败，不冒充科学PASS。
- 核实保存prefix缺原目标/最终query/完整后缀，执行可做的真实缓存CPU测试；冻结8场景32表达、原生fixed-query prediction_head任务入口、原配对/目标、组分母及场景均衡统计，完成语法/统计fixture。原生GPU任务次数0，尚无实际mask诊断。
- 17:32:27核实原M204在server4GPU0持续训练，原生Train[8/50]676→679/4686；恢复日志新增mIoU0.457和0.461（3位小数，精确新best未知）。仍低于历史0.5020，不能称完整训练收益。server3GPU1在本轮17:05:39被外部作业占用；未迁移、共享、驱逐或重启。
- 本轮实际产出：1新诊断、3类CPU数值/缓存测试、1统计fixture及待GPU原生任务包；0新增科学PASS/准入/训练。用量收据窗口为本轮begin至receipt，当前用量未知，不重复叠加缓存/推理，也不当账单。完整六段报告待渲染、finish待验证。

## 5. Decisions Made
- 主线仍是不同层级消息如何真实更新点/超点特征并影响mask；显存只是资源约束，不把图活性/高精度代数/早期VAL当机制有效性。保持原1e-6、原目标0.5100及冻结方向。
- 本轮新诊断按真实exclusive_gpu_slot停放server4；GPU任务前已完成可执行非GPU准备。1小时内或真实资源变化后以原稳定ID续跑原生同设备控制；失败继续如实保留，不能放宽阈值。
- 四个辅助human-scope hold原retry18:39:42上海未到，不重复复查或索取已执行的CPA恢复授权。仍有准备预算，不伪称储备满/预算0，也不造第二个同义变体；未声称所有独立路线耗尽。
- 本轮执行完成与科学有效性分开；仅finish显式通过且核实租约/待提交状态释放后才称完成。新M204结果仅为早期恢复进展，不替代最终配对评估。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
