# Research Pipeline Report - cluster_project
快照时间：2026-10-19T10:10:01.164628+00:00；生成报告时快照年龄：1577 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-19 18:10:00
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
================================================== 2026-10-19 18:09 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1] Best=0.4752 9/50 no_improve=0/10 gpu=0 ? 序列: 0.4571, 0.4609, 0.4752

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
- 研究储备 1 / 2；储备准备预算 1，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 4、待资源 0、未分类阻塞 1。
- 非终态候选与排队项合计 5；总上限 8。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 122：complete=25 / rejected=91 / blocked=5 / training=1。
- 否决范围：unclassified=91；实现修订累计 5；收据文件 10（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T10:39:42.055835+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T10:39:42.055835+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T10:39:42.055835+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T10:39:42.055835+00:00 |

## 4. This Tick's Actions
- 本轮快照18:10:01上海，未重复预检；先登记1个不同于尺度删除的表达特异点消息诊断，再定向核对已完成M202双线性能量诊断边界。固定原query，只用同场景不同原目标表达的现有完整点消息作因果对照，不设计新门控/路由/监督或训练变体。
- 对真实M95两场景8表达prefix执行CPU移植/撤销对照：有效接收点729/1185，padding及三尺度ID对应全部相同，identity和移植后恢复逐位一致；消息RMS差异0.147421至0.251901。仅说明介入非完全相同消息，缓存无原query/目标/物理坐标，不能当任务收益或科学PASS。
- 冻结原8场景32表达的原生ILA/prediction_head固定query消息移植入口、原主目标匹配、坐标/索引/撤销identity严控及场景均衡读数；完成语法、donor选择、空组及不重复加权fixture。原生GPU任务执行0、新科学PASS0、准入0、新训练0；既有尺度诊断严格数值失败全部保留。
- 18:24:41新鲜核实server4GPU0被M204及三锁占用，原生Train[9/50]4571→4575/4686；begin监控best约0.4752，仍低于历史0.5020。server3SSH/hostname正常但GPU1的nvidia-smi/contexts/inventory均返回255，报0000:4B:00.0设备句柄UnknownError，当前UUID/占用未知，不能沿用旧忙碌记录或推断空闲。原slot脚本失败与修复后的只读采集均保留，未重置/驱逐/重启或使用未授权卡。
- 实际产出1新诊断、1真实缓存CPU测试、1统计/语法fixture及待GPU任务包；旧尺度ID仅补实际资源变化。完整用量收据待finish，本地begin到receipt部分窗口之外及最终回复不含在内，未知不记0，cache/input与reasoning/output不重复相加也不当账单。本报告保存时finish尚待核验。

## 5. Decisions Made
- 新信息缺口是点侧消息是否在固定原query条件下携带有用的表达特异任务信息，不是重新包装rank、边界/冗余关联、语言路由或query选择。CPU差异只为可执行性准备；真实mask效果、创新与有效性仍未验证。
- server4忙与server3设备查询故障构成当前混合external_resource阻塞；两主线候选均先做完可执行非GPU准备再停放。按真实变化更新旧exclusive标签，不伪称两卡均忙、不更改skill分类器或准入规则。恢复后仍需新鲜UUID/空闲/独占锁/冻结资产及原1e-6控制，失败不放宽。
- 保留M204现有训练及已执行授权，不重启、不迁移、不改数据/seed/schedule/模型；保留四辅助scope hold，不因定时器到期恢复监督主线或M201，不重复索要已完成的CPA恢复授权。
- 本轮不宣称独立路线耗尽或科学设计成功。只有finish显式通过并核实上下文提交及租约/待提交状态释放，才称本轮检查完成；否则保留证据后abort。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
