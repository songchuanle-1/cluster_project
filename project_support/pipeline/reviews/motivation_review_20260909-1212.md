================================================================================
  Motivation Review - cluster_project
  2026-09-09 12:12 Asia/Shanghai
================================================================================

## 1. Goal
Binding goal.json, reproduced completely:
```json
{
  "metric": {"name": "mIoU", "target": 0.51, "dataset": "ScanRefer"},
  "baseline_experiment_id": "model_base1",
  "description": "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51",
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
    "FLOPs ≤ 10.0G; 峰值显存 +15% 需 ≥+0.003 mIoU 才保留",
    "整体统一修正前禁止单变体改 schedule (epochs=50/max_iters=70 不一致暂保持)",
    "【Phase1 硬性·用户 07-28】Phase 1 禁止调参。只允许结构性机制变更 (新 forward/新 loss/新模块/结构消融)。所有候选变体入队前必须通过 autonomous_design.md Phase 1.6 调参气味检测。禁止: 超参扫参、纯 config 变体改数值不改结构、'在X处加一个LayerNorm/Linear/Scaling'式微调(参数<5K且无新计算图)。解除需用户明示。",
    "分支停止: 提升 <0.002 且收敛平台不升 → 停该分支",
    "机制声称(更新): context 需 A1−A0≥0.005 [✓已确认 0.0118]; routing 需 A3−A1≥0.002 [✗已证伪 -0.0544]; A4-shuffle 对照待定 (running)",
    "收敛定义: 近5次验证均值Δ<0.001 且5连不刷Best; 结构首筛统一 seed 1999",
    "【已解除·用户 08-10】原'cluster只更新inst_feats/仅最后1层'约束解除 — 突破方向: ①cluster context 调制 decoder query ②多层注入. 保留: 禁 N² attention",
    "效率测量: bs=1 warmup20 repeat100 median/P90; 实测延迟/显存为主, FLOPs 为辅"
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
  ]
}
```
check_goal12:09:50:Phase1 NOT YET; M95=.5020, target=.5100, gap=.0080.
Historical findings statuses do not override current ledger or live processes.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context helps, explicit point routing hurts | supported | A1/A0+.0118; A3=.4468, A4=.4941 | Do not reopen routing |
| Coherent fine branch contains useful context | suggestive | M169=.5000, Acc50=.554, spm=.462 | Partial-patience and recurrence confounds |
| Recurrence is needed for branch retrieval | untested | M169 used five feedback boundaries | Separate hierarchy content from feedback |
| Terminal-only retrieval works | untested | M184-M187 waiting | No fine-first single-branch terminal candidate |
| Fixed ancestor query initialization helps | running | M183 launched12:08 on GPU1, epoch1 | No completed validation |

## 3. Experiment Assessment
Read current CSV and extracted metrics/conclusions across218 analysis documents;
older duplicate, placeholder, unpaired or conflicting measurements remain qualified.
The prior review20260908-1917 provides family-level provenance, not new results.
| Experiment/Family | mIoU | Relation To Motivation | Contribution |
|-------------------|------|------------------------|--------------|
| A0/A1/A3/A4 | .4894/.5012/.4468/.4941 | Context versus routing | Context supported; point routing closed |
| Gate/FiLM/normalization/score sweeps | below champion | Numerical modulation | Banned, no expansion |
| Detail/residual/CCP/reaggregation | <=.5008 | Context delivery | No robust additive gain |
| CTF-HCG/M95 | .5012/.5020 | Comparison platform | Preserve protocol; seed-fragile |
| CSORT/MLay/MFP seed controls | about.487-.496 | Robustness | No causal single-seed claim |
| DCA/DCM/DCMV/DUAL | <=.5010 | Attention access | Closed; no added attention |
| M110-M158 memory/loss/token/writeback | <=.5010 | Additional mechanisms | Closed or supporting only |
| M159/M160 | .4840/.4910 | Geometry | Closed |
| M161/M162 | .4920/.4980 | Aligned versus shuffled mask retrieval | Recursive feedback may be a confound |
| M163/M166/M167/M168 | .4899/.4899/.4910/.4900 | Generic feedback | Do not tune weights or scores |
| M164/M165/M171/M173 | .4950/.4911/.4936/.4921 | Hierarchy/competition | stopped_unknown, descriptive only |
| M169 | .5000 | Fine-first coherent ancestry | Best recent branch clue, not proof |
| M170/M172 | .4970/.4966 | Contrast/stable support | Below champion |
| M174/M177 | .49349165/.49627879 | Consensus/bottleneck | No better path-score evidence |
| M175/M176/M178 | interim | Other hierarchy selection | Over10G; no qualified promotion |
| M179-M182 | N/A | Original reserve topologies | Withdrawn for resources, never trained |
| M183-M187 | no terminal result | Initialization/terminal retrieval | Preserve active run and FIFO |
M169's old analysis calls stopping normal at26 with11 no-improvements; corrected
parser evidence invalidates full-patience claims. No retrospective rerun here.

## 4. Gap Analysis
Q1: Can a fine-first single ancestry branch aid the final prediction without
its own earlier reads changing the mask that selects that branch?
M184 selects a coarse subtree, M185 averages full paths, M186 transports mass,
M187 covers several fine branches. None preserves M169's one fine argmax path.
M183's launch reduced eligible reserve5->4, below capacity4+1.
No active global hold appears in goal constraints or latest10 decision records.

## 5. Design Rationale
Q2: M188 removes four intermediate MQ feedback edges from an independent M169
copy, retaining the unchanged fine-occupancy argmax and ancestor-chain mean
immediately before the final decoder. This tests recurrence, not which depth
or numeric setting scores better. No arbitrary index/count sweep follows.
Q3: An improvement beyond M95 would motivate validation of terminal single-path
context; a plateau would close this terminal branch without numeric tuning.
The terminal boundary derives from the last supervised prediction.
Argmax is deliberately hard: mask-selection gradient is absent, while query,
selected point features and projection receive gradients. No straight-through
estimator, softmax relaxation, new temperature or loss coefficient is added.
Prior results are descriptive because stopping histories and seeds limit causality.

## 6. Next Batch
See designs/exp_design_20260909-1212.md: M188-CTF-HCG-CSORT-MQB-TR only.
Require independent package/config, graph and selection tests, measured<=10G,
matched bs1/warmup20/repeat100 profile, safe sync to both servers, then FIFO enqueue.
Preserve M183 and all other active code, resource policy, checkpoints and schedules.
================================================================================
