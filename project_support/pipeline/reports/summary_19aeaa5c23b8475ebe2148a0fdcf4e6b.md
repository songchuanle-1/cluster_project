# Research Pipeline Report - cluster_project
快照时间：2026-10-18T02:09:47.439032+00:00；生成报告时快照年龄：829 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-18 10:09:46
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
================================================== 2026-10-18 10:09 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1] Best=0.4885 20/50 no_improve=6/10 gpu=0 ? 序列: 0.4820, 0.4862, 0.4851, 0.4856, 0.4816

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
| M203-FLE | configs/Quard/ctf_hcg_csort_fle_r1/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | running |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 1（运行 1 / 认领 0 / 等待 0）；目标 2；准入预算 1。
- 研究储备 6 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 候选累计记录 112：complete=14 / rejected=91 / blocked=6 / training=1。
- 否决范围：unclassified=91；实现修订累计 3；收据文件 10（含修订或重试，不代表成功率）。

## 4. This Tick's Actions
- 本轮不可变快照为上海时间2026-10-18 10:09:47/design，原截止11:09:47不改；核实实际会话身份与前台归属、后台调度禁用、24约束/11禁止及原资源授权。第0-3段保留preflight时点。已先登记fle-backward-saved-neighbor-storage-audit，再执行有限诊断；不是新增模型或参数搜索。收尾待finish。
- 10:15:51只读确认M203-FLE在server4物理GPU0第20/50轮，原生步4140至4150/4686增长；19次原生VAL，早期best0.48853155970573425，仍低于baseline0.4894、历史M95 0.5020及目标0.5100，历史目标差距0.0080不变。没有额外VAL、checkpoint选择、训练变更或终态结论。
- 实际执行一个不同于旧几何/连续性测试的有限效率诊断：K32/H8/C256/float32保持生产值，4种预注册人工输入。按底层storage指针去重并单列输入别名后，最大新增浮点gather存储在N16/64/128分别为524288/2097152/4194304字节，随N线性增长；N128分16个8点叶虽仅1024有效边，仍分配4096槽且最大gather仍4MiB。
- 12次CPU exchange及8次CPU特征梯度执行；hook/普通/no_grad前向逐位一致，匹配梯度最大差0且有限非零。N128的新浮点保存总量4456448字节包含诊断square-mean读出，不能当作完整原生激活、分配峰值或CUDA显存。没有已实现的显存节省或资源PASS；参数减少与激活成本不能混为一谈。
- 9个生产源文件和部署配置哈希未变；server4 CPU单线程，CUDA隐藏且未初始化。无旧测试重跑、TRAIN预处理、checkpoint加载、FPS、原生网络前后向、optimizer步、分块/checkpointing实现、模型修订、准入、部署或新启动。
- 10:15:51-52两张授权卡均占用：server4 GPU0由M203及三锁持有，server3 GPU1是外部任务。两项原生诊断保留原冻结资产、checkpoint、cohort及1e-6容差，以真实资源表续等。此前10:01只读看到server4 GPU1空闲，但用户仅询问空闲情况、尚未同意扩大授权；本轮未使用或计入容量，不共享/驱逐/reset/删锁。
- 本轮留档时实际到期并按ID核对的辅助授权hold数量为4；只核对原解除条件，未出现新优先级恢复授权或主线必需的辅助证据，原范围与科学门槛保留，已到期者按原四小时界限再查。不因到期或空槽重开、恢复M201或派生变体。
- 实际产出为一个有限CPU存储诊断、4条件/12算子调用/8特征梯度执行、两项资源核实、实际到期的授权复查及审查/设计/记忆/报告。收据用量窗口仅本轮begin至收据，不含先前读取、晚到记录及最终答复；生成前总量未知。缓存属于输入、推理属于输出，不重复相加、不当账单或科学收益。

## 5. Decisions Made
- 有限诊断complete只表示源算子的该记账问题已执行，不表示新机制有效、峰值显存更低或模型通过准入。效率仍是主线约束，不替代不同层级真实点特征更新的核心贡献；M203原训练保持。
- 后续先完成两个既有原生几何及自身/非自身内容mask诊断；真实空闲授权卡、固定身份、目标资产、当前租约和三锁满足才执行原协议。server4 GPU1未授权，server3备选仍需目标运行时/数据验证。
- 可执行有限CPU核对已实际完成；剩余原生工作有真实外部资源阻塞，以external_resource_blocked收尾，不宣称路线耗尽、为deadline凑变体或放宽科学门槛，不修改目标/授权/调度。
- 完整六段留档后执行finish，核实收据FINALIZED、context提交及租约/待提交文件释放；否则保留证据并具体修复或abort。当前没有训练终态、原生新结论、资源释放或新增用户动作需求，例行心跳保持安静。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
