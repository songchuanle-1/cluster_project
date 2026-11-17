# Motivation Review — cluster_project
Created 2026-10-20T15:58:56.635610+00:00; candidate `hierarchy-reversible-sibling-token-transport`. 原始目标文件 SHA256 0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85。

## 1. Goal
目标 mIoU≥.5100，历史最佳M95=.5020，差.0080；完整冻结目标如下，全部原约束沿用。
```json
{
  "metric": {
    "name": "mIoU",
    "target": 0.51,
    "dataset": "ScanRefer"
  },
  "baseline_experiment_id": "model_base1",
  "pipeline_policy": {
    "research_on_capacity_gap": true,
    "steady_ticks_before_design": 1,
    "design_interval_hours": 1,
    "fill_to_capacity": true,
    "design_buffer": 0,
    "max_candidates_per_design_tick": 4
  },
  "description": "cluster: 面向 ScanRefer 三维语言定位，回归用户最初的点云特征更新主线，研究不同层级承担不同注意力/信息交互作用的轻量结构机制，目标 mIoU ≥ 0.51。核心路径是分层信息交互真实更新点云/超点 inst_feats，再与 query 特征共同生成 mask；不能把仅修改监督损失、沿用已有层级骨架或无效路由计算称为该主线创新。以多尺度 context-only 和 M95 为既有对照，先诊断层级互补性、局部细节及跨层信息是否真正进入 mask 特征，再依据证据选择一个可推导、可证伪的结构机制。监督与关系绑定仅作辅助诊断/匹配对照，不再取代主线。覆盖机制对照、泛化稳健性和同口径效率验证；已有收益不证明新的分层注意力有效，也不自动重开历史失败或禁止的路线。",
  "research_mainline": {
    "authorized_on": "2026-10-15",
    "authorization": "用户澄清原始主线为不同层级采用不同注意力的点云特征更新，并明确要求：后续进行纠正吧。",
    "primary_axis": "hierarchical_attention_point_feature_update",
    "auxiliary_axes": [
      "referent-supervision diagnosis",
      "relation/boundary mechanism-matched controls"
    ],
    "roadmap": "docs/research_mainline_correction_20261015.md",
    "legacy_work_policy": "保留旧候选、证据与科学状态。四个监督候选仅为辅助证据，不再因到期或空槽而优先续做、准入或派生；不自动恢复 M201。先审计 M95 层级信息流和 inst_feats 写回，再用固定 TRAIN 样本/checkpoint 诊断一个特征问题，按原契约选择和准入一个核心结构机制。"
  },
  "findings": {
    "A0_baseline": "model_base1 = 0.4894 (无 cluster)",
    "A1_context_only": "champion Lite = 0.5012 (多尺度 context 按 ID 回写, 路由算了但 _cluster_to_points 丢弃不用 → 实质 context-only)",
    "A3_routing_active": "TrueRoute = 0.4468 (路由索引真影响 message) → 比 A1 低 0.0544, routing 生效反害",
    "context_claim": "A1−A0 = 0.0118 ≥ 0.005 ✓ 确认 (多尺度 context 有效)",
    "routing_claim": "A3−A1 = -0.0544 < 0.002 ✗ 证伪 (routing 无独立收益, 反有害)",
    "A4_shuffle_control": "running(07-20 13:03 启动, 0.3900@ep4 early) — 验证 A3 的崩是内容路由有害还是结构注入有害",
    "D1_detail_relause": "D1-detail(relaunch)=0.5003@ep28 stopped_unknown — 距 champion 0.5012 仅 0.0009, detail 单独有效(γ=+0.0109); detail > detail+residual(E4=0.4944)",
    "E4_res_detail_terminal": "E4-residual+detail=0.4944@ep23 stopped_unknown — residual与detail无协同, residual上限~0.4944(=B5单独), 组合无增益",
    "pending_mechanisms": "M1-QGC(query-gated context, running 07-20 16:03); M6-QSF(waiting); M16-CSR(waiting); M17-ORT(orth reg, waiting)"
  },
  "constraints": [
    "[USER-MAINLINE 2026-10-15] 用户授权纠正后续方向：主线为不同层级承担不同注意力/信息交互作用，真实更新参与 query 与 mask_feats 生成 mask 的点云/超点 inst_feats。本条取代 USER-SCOPE-B 2026-09-16 将 referent-supervision 作为 primary direction 的优先级，但保留其诊断证据与辅助价值。旧四个监督候选及 M201-BPS 不再因自动到期/资源空槽而优先续做、恢复或派生；先开展点云特征路径的诊断与机制设计。不得把方向调整记为候选被科学证伪，不自动重开 rejected/withdrawn/banned 路线。全部既有科学准入、资源、Phase1 禁调参、固定数据/seed/schedule、验证边界和部署契约不变；资源授权和调度不变。",
    "【用户 2026-09-15 23:33·运行位置更新】本项目训练、原生数据诊断、行为验证及资源测试允许在 server-4 GPU0/1（每卡1槽）及 server-6 GPU7（2槽）执行，总容量4，以 SERVERS.yaml 为准。此授权取代此前 server-4-only 限制；其他服务器/GPU不授权。本地仅编排、编辑及静态检查。执行前检查实际占用和显存，不驱逐外部任务，不改变科学准入或其他项目配置。",
    "资源门槛必须采用与历史 baseline/champion 一致、可复现的同口径统计：按既有标准口径判定总 FLOPs ≤ 10.0G，并同时报告候选机制相对 baseline/champion 的增量 FLOPs、延迟和显存。不得用仅对新候选启用、且会使 baseline/champion 自身不合格的补充计数单边拒绝候选；若采用更完整的新口径，必须先同口径重测 baseline/champion，再按相对增量和重新校准的统一阈值审查。峰值显存 +15% 需 ≥+0.003 mIoU 才保留",
    "整体统一修正前禁止单变体改 schedule (epochs=50/max_iters=70 不一致暂保持)",
    "【Phase1 硬性·用户 07-28】Phase 1 禁止调参。只允许结构性机制变更 (新 forward/新 loss/新模块/结构消融)。所有候选变体入队前必须通过 autonomous_design.md Phase 1.6 调参气味检测。禁止: 超参扫参、纯 config 变体改数值不改结构、'在X处加一个LayerNorm/Linear/Scaling'式微调(参数<5K且无新计算图)。解除需用户明示。",
    "分支停止: 提升 <0.002 且收敛平台不升 → 停该分支",
    "机制声称(更新): context 需 A1−A0≥0.005 [✓已确认 0.0118]; routing 需 A3−A1≥0.002 [✗已证伪 -0.0544]; A4-shuffle 对照待定 (running)",
    "收敛定义: 近5次验证均值Δ<0.001 且5连不刷Best; 结构首筛统一 seed 1999",
    "【已解除·用户 08-10】原'cluster只更新inst_feats/仅最后1层'约束解除 — 突破方向: ①cluster context 调制 decoder query ②多层注入. 保留: 禁 N² attention",
    "效率测量: bs=1 warmup20 repeat100 median/P90; 实测延迟/显存为主, FLOPs 为辅",
    "【用户 2026-09-10·后续实验涉及面】新增研究必须覆盖: 错误诊断、核心机制与公式推导、原始文献新颖性核对、机制匹配对照、泛化与稳健性、效率。先用固定样本及已有 checkpoint 诊断候选覆盖/边界、同类辨别/关系绑定、多尺度证据重复；报告分母、样本清单和缺失数据，不凭总体 mIoU 猜瓶颈。依据诊断选择一个主机制，不把多个候选问题同时变成变体队列。操作细则见 docs/experiment_scope_20260910.md；本文件为约束主源。",
    "【用户 2026-09-10·新设计准入】每项新增核心机制需明确具体错误及证据、变量与假设、目标或约束到 forward/loss 的逐步推导、梯度/退化情况/复杂度、与已核实原始论文及历史失败变体的差异、匹配对照和预先否决条件；未核实项必须标为未完成。诊断/复现/对照不要求各自新颖，但必须关联核心问题，不能冒充独立创新。先 motivation_review 再 exp_design，沿用模板并补充这些字段；未完成科学准入的机制不得训练入队。",
    "【用户 2026-09-10·执行优先级】新设计科学准入优先于队列深度补足。没有合格候选时继续数据诊断、推导、原始文献核对或离线正确性检查，记录缺口，不为填满 GPU 批量扩展 selector/pooling/回写变体。非全局暂停，不改 cron 或现有运行状态；已入队 M188/M189/M190/M191/M193 保留原 FIFO 和原准入，定位为旧路线验证，不自动生成后继同类变体。",
    "【用户 2026-09-10·验证边界】主机制须报告总体指标和预先定义的错误子集/负对照；按场景统计不确定性，禁止用测试集选机制。oracle 只用于诊断上界，不作为可部署结果。泛化/稳健性纳入设计，但不自动授权新数据集训练、额外标注或多 seed 扫描；Phase1 首筛 seed1999 和既有 schedule/资源/banned 保持，Phase2 达标后仍先提交确认方案。未验证的效果与新颖性不得写成结论。",
    "【用户 2026-09-14·容量补齐授权】当 running+claiming+waiting 小于 SERVERS.yaml 计算出的容量，且连续 2 个健康 tick 没有新的终态证据或可执行诊断时，按缺口自主设计并入队结构性候选，本轮最多 4 个。每个候选必须对应可区分的错误证据、因果假设或机制分支，并分别完成 motivation_review、exp_design、调参气味检测、独立 model/config 校验、行为/资源测试、代码同步和决策日志。禁止纯调参、重复 seed、纯消融、已证伪/withdrawn 路线、历史变体改名和无证据占位。若合格候选少于容量缺口，允许保留空槽并记录淘汰原因；该条款不改变 FLOPs、显存、Phase1、banned 和验证边界约束。",
    "[USER-SCOPE-B 2026-09-16] Open the referent-supervision axis. Supervision-level structural changes for the referent decision (new loss / new positive-set definition / new supervision unit) are re-admissible as the project's primary direction. Basis: the two 2026-09-13 route_change decisions (20260913-061110 and 20260913-071026) excluded supervision repair and relabeling on the stated ground 'descriptive association is not causal evidence' while declaring scientific admission incomplete. That ground was removed on 2026-09-16 by a causal intervention on the fixed M95 checkpoint in one same-forward capture that changed only the selection rule: restricting selection to the native training-positive set gives +17.9pp scene-balanced (87.0 vs 69.1, 95% CI [+10.9,+25.8], 22 fixed / 0 broken), while the objectness-only control (seed inside ANY instance) is exactly null. All other constraints and every banned[] entry stay in force unchanged: Phase1 no-tuning, FLOPs<=10G, peak memory, validation boundaries, scene-level uncertainty, pre-defined rejection criteria, and the full motivation_review -> exp_design -> smell-check -> independent model/config -> native backward -> resources -> independence -> admission receipt -> safe sync chain. RefMask3D, DETR and other existing work must not be presented as this project's contribution: exp_design must state the whole-mechanism difference against the verified originals and the increment over generic mask-aware matching.",
    "[USER-ALLOCATION 2026-09-16] The project's training and native-diagnostic allocation is now server-6 GPU7 ONLY, with 2 task slots (SERVERS.yaml allowed_gpus [7], max_tasks_per_gpu 2), so the design capacity is 2 rather than 4. server-4 GPU0/GPU1 are removed from this project's whitelist (allowed_gpus []); its current foreign jobs were never touched and are no longer treated as project capacity. Every other constraint is unchanged: the operating-location rule of 2026-09-15 is superseded only for the host list, and all science, resource, schedule, validation, banned and closure requirements still apply. Local remains orchestration/edit/static only.",
    "[USER-ALLOCATION 2026-09-20] Supersede the 2026-09-16 allocation for all NEW training and native diagnostics: dispatch only to server-4 GPU0 and GPU1, one task per GPU, total design capacity 2. server-6 GPU7 is dispatch-disabled and contributes zero capacity. Grandfather the already-running M197-PIRS on server-6 GPU7 for monitoring and natural completion only; do not launch any successor, diagnostic, restart, or new task there. Do not stop M197 merely for migration. server-4 currently responds to ping but refuses SSH on port22, so no launch or sync is allowed until SSH, GPU occupancy, code root, environment and data paths are successfully verified. All scientific, resource, schedule, validation, banned and closure constraints remain unchanged; local remains orchestration/edit/static only.",
    "[USER-ALLOCATION 2026-09-21] Supersede the 2026-09-20 allocation for all NEW training and native diagnostics: dispatch only to server-6 GPU7, with max_tasks_per_gpu=2, so total design capacity is 2. server-4 GPU0/GPU1 are removed from the project whitelist (allowed_gpus []) and dispatch_enabled=false; its foreign jobs are never touched and are no longer project capacity. M197-PIRS remains stopped_unknown and must not be restarted automatically; any safe resume still requires the full checkpoint, runtime, resource, backward and admission chain. Before any launch or sync, verify server-6 SSH, actual GPU7 occupancy/memory, code root, conda environment and data paths; do not evict external jobs. All scientific, resource, schedule, validation, banned and closure constraints remain unchanged; local remains orchestration/edit/static only.",
    "[USER-ALLOCATION 2026-10-14] Latest explicit user request: move training to server4. Verify pinned SSH identity dl04-MS-7E06 at 192.168.1.115. Live inventory has ONLY GPU0 RTX5090 UUID GPU-7f82edb9-f620-8045-caea-a75232265cd1; authorize this one GPU with one slot, not historical GPU1. Disable new dispatch on server-6; retain the exact existing M201-BPS source process until target code/environment/data/full-checkpoint/native backward readiness is verified, then migrate the SAME experiment using native --resume with optimizer/scheduler/best/patience state. Preserve dirty files and foreign jobs. No cold restart, scientific gate change, schedule change, dataset change, new seed or scheduler change is authorized. Local remains orchestration/edit/static only.",
    "[USER-ALLOCATION 2026-10-16] User explicitly authorizes moving cluster_project to server-3 GPU1 when server-4 is blocked. The current server-4 GPU0 is blocked by live NVML occupancy and its original training flock. For the current fallback use only server-3 GPU1, one task slot and total dispatch capacity1; pinned hostname sysu311-MS-7C59 at192.168.1.194, RTX3090 UUID GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0. Disable new dispatch on server-4 and server-6 while preserving their jobs, logs, checkpoint state and resource evidence. This changes resource placement only: the point-feature mainline, auxiliary scope holds, scientific gates, original failures, data/validation boundaries, seed1999, epochs50/max_iters70, FLOPs and relative memory requirements remain unchanged. Verify target runtime, exact frozen assets, native execution, actual GPU idleness and exclusive lease before using GPU1; no GPU0 use, eviction, reset, stale-lock deletion, automatic M201 recovery, cold restart or scheduler change. Local remains orchestration/edit/static only.",
    "[USER-ALLOCATION CONFIRMED 2026-10-16] User explicitly confirms: 后续都是用server3的gpu1. All FUTURE cluster_project training and GPU diagnostics use server-3 physical GPU1 ONLY, one slot, including after server-4 becomes available; this supersedes the conditional fallback in the preceding allocation entry. Fixed identity remains sysu311-MS-7C59 / RTX3090 UUID GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0. The currently verified address is192.168.1.120; old192.168.1.194 is historical, not the dispatch destination. server-4/server-6 stay new-dispatch-disabled; preserve their existing jobs and evidence. No other GPU, automatic M201 recovery, reset, eviction, lock deletion or scheduler change. This confirmation changes future resource placement only: all prior scientific constraints, failures, seed/schedule/data/validation boundaries, point-feature mainline, auxiliary holds, lightweight budgets and training admission gates remain unchanged.",
    "[USER-ALLOCATION OVERRIDE 2026-10-16] Latest direct user instructions: server4 恢复双卡了  你可以使用单张  使用GPU0 继续运行实验; then server3的gpu1也可以继续沿用. Supersede the preceding exclusive server-3 placement: authorize server-4 physicalGPU0 AND retain server-3 physicalGPU1, one task per card, total capacity2. Strict known-host SSH confirmed dl04-MS-7E06 at192.168.1.115 with twoRTX5090; CURRENT server4GPU0 UUID isGPU-958e741a-e5cf-127e-ffe8-9b984e1f404c. OldUUID GPU-7f82edb9-f620-8045-caea-a75232265cd1 is now server4GPU1 and is NOT authorized. Retain server3GPU1/sysu311-MS-7C59/192.168.1.120/UUID GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0. server3GPU0,server4GPU1 and new dispatch on server6 remain unauthorized. Verify live occupation, exclusive leases, runtime, native assets and scientific admission before each computation. Preserve foreign/existing jobs and all failures; no reset, eviction, lock deletion, automatic M201 recovery, duplicate experiment launch or scheduler change. This changes resources only, not10G, implementation revision bounds, scientific gates, fixed seed/schedule/data/validation, point-feature mainline or auxiliary scope holds.",
    "[USER-FLOPS-EXCEPTION 2026-10-16] User explicitly accepts the small measured overrun for SAME m95-hierarchical-mask-feature-path-audit / M202-HDS: 10.034588748G counted FLOPs (0.34588748% above 10G), bound to the exact ten tested source/config hashes and passed revision2 in pipeline/authorizations/hds_flops_exception_20261016_04dd082c.json. This prospective candidate-specific exception supersedes ONLY its default10G rejection; the default10G for every other realization, original failed evidence, two-revision limit, memory/latency review, all other gates/bans, seed1999, schedule, data/validation boundaries and server3GPU1/server4GPU0 permissions remain unchanged. No code change/revision3 is authorized.",
    "[USER-ALLOCATION ADDITION 2026-10-19] Direct human reply in the owning chat authorizes server-4 GPU1 for cluster_project experiments: 授权GPU1 可以做实验. Add physical GPU1 UUID GPU-7f82edb9-f620-8045-caea-a75232265cd1 at pinned dl04-MS-7E06 /192.168.1.115 to server4 allowed_gpus[0,1],one task per card. Preserve server4GPU0/M204 and retained server3GPU1 allocation;server3GPU0 and new server6 dispatch remain unauthorized. This supersedes ONLY the prior prohibition on server4GPU1,not scientific admission,10G/default Pareto budgets,Phase1 no-tuning,existing failures/revision bounds,fixed data/seed1999/epochs50/max_iters70,point-feature mainline,auxiliary scope holds or scheduler policy. Verify live UUID/idleness/exclusive lease/runtime/assets before GPU use. No reset/eviction/automatic M204 or M201 restart,cold start,migration or unrelated code commit is granted. Authorization record:pipeline/authorizations/server4_gpu1_20261019.json."
  ],
  "banned": [
    "gate系 (cag/cfe/layerscale 三连败)",
    "语言路由系 (langroute/langc2f/scale <+0.002)",
    "attnpool/qcond/agg/multi (复杂度无优势)",
    "prune (先单独修 benchmark)",
    "nomask 扩展 (19.9G 仅作上限对照)",
    "3/4/6 层重复注入 (已证退化)",
    "大型 Q/K/V/O 投影 (与轻量目标冲突)",
    "Phase1 调参系 (orth_weight 扫参/topk 扫参/nhead 扫参/scale 增减/init 扫参/layer_num 扫参/dropout 改值/activation_fn 改值/改数值不改结构 → 进 Phase 2 再说)",
    "【Phase1 调参原则·用户 07-30】以下均视为调参, 不受 banned 列表穷举限制: (a) 参数增量 <5K 且无新计算图结构 (Linear(d,1)/LayerNorm/learnable scalar); (b) 唯一变化是改变数值分布(归一化/缩放/温度系数)不改信息流; (c) 超参无推导依据('先试0.1'); (d) 变体可概括为'在X处加了一个{单层/单算子}'。判定标准见 autonomous_design.md Phase 1.6",
    "true_route / 显式 routing 注入 (A3=0.4468 已证 -0.054 有害, 除非 A4-shuffle 证明内容路由有效)",
    "residual 系 (B5=0.4944, E4=0.4944 — 上限固定, 与 detail 组合无协同)"
  ],
  "resource_exceptions": [
    {
      "candidate_id": "m95-hierarchical-mask-feature-path-audit",
      "experiment_id": "M202-HDS",
      "authorization": {
        "path": "pipeline/authorizations/hds_flops_exception_20261016_04dd082c.json",
        "sha256": "e2b39c6560d642a647935079a988afa8977ef2cf63f455c9e0d6eb51d44e8a60"
      },
      "max_standard_counted_flops": 10034588748,
      "implementation_revision_sha256": "73ec1df2a4c6e1de50d8614c0fce0e4e41437c29321af2d858c2b81a3f5d7441"
    }
  ]
}
```

## 2. Story Status（故事线状态）
| 假设 | 状态 | 证据 | 缺口 |
|---|---|---|---|
| 多尺度context有效 | 既有结果支持 | A1 .5012 vs baseline .4894 | 不证明新注意力有效 |
| 直接细叶间依赖缺失 | 计算图支持 | 原CTF每token FFN后直接gather；祖先mean仍含间接信息 | 不称完全没有邻叶信息 |
| sibling交换改变实际mask | 固定诊断支持 | 本轮32表达正确vs严格错配均非零，identity0 | 完整native backward、资源、重复性尚未测 |
| 新结构提高任务质量 | 未知且有不利旗标 | content前景7/8场景变差；比等质量错配6/8更好 | 训练质量未知，不据小样本宣称收益 |

## 3. Experiment Assessment（已有实验的动机视角评估）
| Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
|---|---|---|---|
| M95 | .5020历史最佳 | 已有CTF/HCG/CSORT基线 | 本轮只用epoch16冻结诊断，不等同最佳checkpoint |
| M39-C2C | .4865历史 | 每尺度全连接投影attention+residual/LN | 不能只重命名token交互；本试验固定同parent图与质量可逆性 |
| HDS/FLE/CPA | 不在本轮重估 | 分别互斥支持/同叶点注意力/point-to-coarse | 保留旧拒绝，不重开 |
| PCE R1/R2/R3 | 未训练 | 物理接触点交换；原数值失败保留 | 本方案不使用接触图，不是PCE额外修订 |

## 4. Gap Analysis（Q1: 故事缺什么）
本轮32580有效超点-表达对中目标常跨细叶；新的task relevant假设是共享祖先池化不能保留“哪个细叶向哪个细叶提供内容”的直接依赖。这里只证明可执行的缺失依赖及对照分离，没有证明池化损失能由此恢复。完整数据分母及全部方向见 `pipeline/diagnostic_bundles/tick_99819673/diagnosis_analysis.json`。已有外部诊断的粗尺度删除/纯bias解释/最终ILA缺失解释不能作本方案效益证据。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
只测试一个固定机制：同一中层parent内的细token质量可逆传输。其信息流不同于M39的全尺度Q/K/V/O+LN，也不同于原mean broadcast。质量约束限制任意全局细叶均值漂移，但不保证后续融合/非线性/logit均值。原生不利前景读出须保留并检验完整源图/损失，不能调温度、gate或挑场景解决。

数学primitive不是贡献：[Hastings1970](https://academic.oup.com/biomet/article-abstract/57/1/97/284580)已有可逆Markov构造；[Sinkformers,AISTATS2022](https://proceedings.mlr.press/v151/sander22a.html)使用Sinkhorn双随机attention。本方案使用不等超点质量的MH而非Sinkhorn，局部树sibling图而非全局全尺度交互；是否有整体论文新颖性仍未完成，不能写首次。

## 6. Next Batch
见 `pipeline/designs/exp_design_20261020-2359_rstr.md`。先完整源图/原生loss反向/同口径资源；没有准入不入队。全部原负面证据与默认修订2次不变。
