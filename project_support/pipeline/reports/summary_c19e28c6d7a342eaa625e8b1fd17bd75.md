# Research Pipeline Report - cluster_project
快照时间：2026-10-16T10:09:30.674701+00:00；生成报告时快照年龄：796 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-16 18:09:30
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
================================================== 2026-10-16 18:09 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1] Best=0.3337 2/50 no_improve=0/10 gpu=0 ?

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
| M202-HDS | configs/Quard/ctf_hcg_csort_hds_canon_r1/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | running |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 1（运行 1 / 认领 0 / 等待 0）；目标 2；准入预算 1。
- 研究储备 4 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 候选累计记录 101：training=1 / rejected=91 / complete=5 / blocked=4。
- 否决范围：unclassified=91；实现修订累计 2；收据文件 8（含修订或重试，不代表成功率）。

## 4. This Tick's Actions
- 本轮前台快照2026-10-16 18:09:30+08为design：活跃1/容量2、等待0、准入预算1、储备4/2、储备预算0、到期候选0。只执行本项目begin已有的一次preflight，不跨项目、不改调度；科学状态training，执行结果待实际finish。
- 原生核验18:15:06与收尾18:20:05：同一server4物理GPU0 PID216566持续训练，最后Train[2/50]2361→2365/4686，GPU UUID与3个生命周期锁正确，未采样到Traceback/OOM。瞬时显存15053MiB已用/17057MiB空闲、利用率38%，不当全程峰值；未占用额外GPU。
- 第1轮原生TRAIN及VAL均已完成，验证363个batch、9508条表达，完整精度mIoU0.3337104618549347，来自18:05日志及checkpoint而不是两个已完成验证轮次。独立scene数量未知，不能把363个batch当363个scene；历史champion0.5020、baseline0.4894、目标0.5100与差距0.0080不变。早期结果不构成提升或最终机制失败。
- 先预注册稳定诊断m202-native-validation-checkpoint-evidence-audit，再在CPU只读当前运行稳定last.pth并校验哈希/读前后stat、实际原生saver/resume函数及tools/train.py一致源文件。模型1165项状态、优化器642项状态及param_groups、scheduler、epoch1/best_miou/epochs_no_improve0均存在；真实best值与日志一致。未实际执行恢复、未重启或中断训练，不把字段存在称为恢复执行通过。
- 保留checkpoint_audit.json首次元数据解析器对numpy.float32的误判。checkpoint_scalar_type_review.json按numbers.Real和有限值复核确认best_miou原本存在且为0.3337104618549347；没有缺字段、模型修订或放宽科学阈值。10项正例/逐一缺字段/非有限值/错误类型schema检查均通过；这是读写契约诊断，不是10次训练实验。
- 实际原生eval AST及本次文件清单确认：scene_ids和pious在内存累计，但eval只返回miou并输出汇总/TensorBoard scalar，没有启用逐表达/scene payload导出。因此当前聚合产物不能支持冻结计划的scene配对95%区间、子组伤害或噪声底结论，均记未测/未知；未伪造区间或用总体mIoU替代。
- 本轮产出是1个完整证据就绪性诊断、真实新验证/连续性/checkpoint证据、10项schema对照和决策日志；新模型变体、新训练准入/启动、模型修订、目标和调度改动均0。完整六段留档；用量仅在收据保留begin→receipt局部窗口，未知如实标注，缓存已含输入、不重复相加，不当账单。

## 5. Decisions Made
- 继续已获准的同一M202-HDS原模型、seed1999、batch2、原loss/optimizer及epochs50/max_iters70；不依据单个早期VAL结果改实现、调参或停止，不因空槽重复启动。
- checkpoint恢复字段就绪不等于已做原生恢复测试；场景级不确定性证据仍缺，继续按已冻结计划收集有效训练后匹配证据，不修改活跃训练循环、不声称已提升。
- 其余4个辅助监督候选仍是既有human_authorization范围保留，未因定时触发或空槽重开。当前design_cycle的external_resource_blocked仅描述这些辅助授权，不是物理GPU阻塞或主线科学路线耗尽；本轮诊断已完成，没有遗弃可执行审计。
- 本轮收尾只在实际finish成功且租约释放核验后称完成；远端长训练继续。下次触发时刻未读取，记未知，不变更已保存自动化或通知策略。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
