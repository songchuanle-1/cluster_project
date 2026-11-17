# Research Pipeline Report - cluster_project
快照时间：2026-10-17T18:09:38.938385+00:00；生成报告时快照年龄：674 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-18 02:09:38
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
================================================== 2026-10-18 02:09 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1] Best=0.4463 6/50 no_improve=0/10 gpu=0 ? 序列: 0.2966, 0.3788, 0.4144, 0.4297, 0.4463

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
- 研究储备 5 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 候选累计记录 109：complete=12 / rejected=91 / blocked=5 / training=1。
- 否决范围：unclassified=91；实现修订累计 3；收据文件 10（含修订或重试，不代表成功率）。

## 4. This Tick's Actions
- 本轮cluster_project不可变快照为上海时间2026-10-18 02:09:38，模式design，原截止03:09:38不改；脚本第0-3段仅对应preflight。实际会话ID匹配配置归属，旧Pipeline-cluster_project仍禁用；目标24约束/11禁止及授权两卡未变。当前收尾尚待finish，不提前宣称完成。
- 02:14:04只读确认M203-FLE仍在server4 GPU0训练，原生epoch6/50从3160增长到3170/4686步。五次VAL mIoU为0.2966073751、0.3788172901、0.4144061804、0.4296720028、0.4462992847；当前早期最佳0.4463，未达到历史M95 0.5020或目标0.5100，历史目标差距仍0.0080。没有新的终态结果或训练效果结论。
- 按ID有限读取并复查四个到期的辅助监督候选：当前主线仍是点云特征更新，没有新的优先级恢复授权或主线所必需的辅助证据，故保留原human_authorization挂起及全部人类判断/科学准入条件。仅记录本次授权核对并按规范四小时限频续查，不把计时到期当作解锁、复活M201或科学证伪。
- 同一次02:14:04资源采集显示两张授权卡仍有任务：server4 GPU0的训练/诊断/独占三锁都归M203原训练，server3 GPU1为外部占用。复用这张真实资源表更新已超过一小时的主线资源等待，不另做等价资源探测，不共享或驱逐，不分配CUDA。
- 主线fle-self-neighbor-content-separation继续沿用上一轮冻结的epoch2 checkpoint、八TRAIN场景32表达、清单与原生runner。本轮没有重跑八类CPU检查、权重加载或CPU数据整理，也没有新的原生前向/反向/优化步、模型、准入或启动；上一轮CPU通过仅是缓存前置证据，不能算成本轮新实验或有效性证明。
- 本轮验证所维护五个ID原有证据引用的真实文件身份，保留全部旧负证据和实现修订；不新做文献/路线重复审查，不制造占位变体。科学状态仍是原生邻域内容机制待测、终态收益未知、新颖性未确立。
- 收据用量窗口仅为本轮begin到收据生成，不含先前读取、晚到记录和最终答复；收据前总量未知，缓存为输入子集、推理为输出子集，不重复相加或当账单。本轮实际产出是四项授权挂起复查、一项复用当前表的资源挂起核实、有限日志/证据记录和报告/记忆维护，不是新增科学实验。

## 5. Decisions Made
- 保持M203原训练与既定终态评估计划。早期验证上升尚非总体性能提升的证据，不用当前VAL选择结构、调参、换checkpoint策略或改损失/容差/目标/调度。
- 主线诊断只在授权物理卡真实空闲、指定主机/UUID核对、新鲜当轮租约与三种生命周期锁、目标资产校验均通过后执行；server3备选仍须目标验证。重试时间是解除条件的后备复查，不是预约卡或承诺调度时间。
- 以真实external_resource_blocked收尾并保留四个辅助授权挂起，不声称独立路线耗尽；当前没有可合法执行且有信息增益的原生测试。按规范冷却，实际资源/目标/新证据变化可提前唤醒，不改自动化。
- 完整六段留档，finish成功且核实释放才称本轮执行完成。训练健康且阻塞未变时按心跳规则保持安静；若校验失败则保留证据、具体修复或abort并核实释放，不谎称科学成功。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
