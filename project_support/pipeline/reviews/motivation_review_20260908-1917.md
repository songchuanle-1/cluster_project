================================================================================
  Motivation Review - cluster_project
  2026-09-08 19:17 Asia/Shanghai
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
Target0.5100; champion M95=0.5020; baseline0.4894. Phase1 at19:09:58.
Old findings statuses are historical; current ledger and live monitor supersede.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context, not routing, helps | supported | A1/A0 +0.0118; A3/A4 negative | Target not reached |
| Recurrent mask retrieval improves grounding | weak | M1610.4920 < shuffle0.4980; M1770.4963 | Recurrence confounds topology |
| Hierarchy structure is useful | provisional | M1690.5000, partial patience | Affordable coherent context |
| Original reserve meets10G | disproved | All M179-M18210.1673-10.1791G | Replace inadmissible graphs |
| Terminal context can avoid intermediate feedback | untested | No self-reinforcing retrieval before last prediction | Explicit recurrence ablation |
| Initial context helps | untested | M183 HQI pending;9.7877G | Complementary placement, no combination |

## 3. Experiment Assessment
Read ledger, 214 terminal-analysis documents and their conclusion sections,
recent designs/bugfixes, decision index and full relevant question/route records.
Some legacy analyses are placeholders or make stronger causal claims than their
data justify. They do not override the binding constraints or exact recent logs.
| Experiment/Family | mIoU | Relation To Motivation | Contribution |
|-------------------|------|------------------------|--------------|
| A0/A1/A3/A4 | .4894/.5012/.4468/.4941 | Context versus routing | Do not reopen routing |
| Gate/FiLM/normalization/pooling sweeps | below champion | Numeric modulation | Banned, no expansion |
| Detail/residual/CCP/reaggregate | <=.5008 | Context delivery | No reliable additive benefit |
| CTF-HCG/M95 | .5012/.5020 | Fixed comparison platform | Preserve protocol, not a robust champion claim |
| CSORT/MLay/MFP controls | about.487-.496 | Seed sensitivity | No seed1999 causal proof |
| DCA/DCM/DUAL combinations | <=.5010 | Additional attention access | Closed; no new attention |
| M110-M118 | .489-.501 | Memory/loss/graph/language conditioning | Closed |
| M140-M158 | <=.5000 | Auxiliary objectives and writeback | Closed or supporting only |
| M159/M160 | .4840/.4910 | Geometry shaping | Closed |
| M161/M162 | .4920/.4980 | Aligned/shuffled feedback | Recurrence may obscure context semantics |
| M163-M168 | .4899-.4950 | Generic mask feedback | Weak; no score/temperature tuning |
| M169 | .5000 | Coherent ancestry | Suggestive, partial-patience caveat |
| M170/M172 | .4970/.4966 | Counterfactual/stable masks | Below champion; no expansion |
| M171/M173 | .4936/.4921 | Competition/inconsistency | Closed |
| M174/M177 | .49349165/.49627879 | Path consensus/bottleneck | No better score evidence; M174 truncated patience |
| M175/M176/M178 | running | Flow/sibling/topdown | Preserve, over10G; no terminal conclusion |
| M179-M182 | no training | Subtree/path/transport/frontier | Withdraw original graphs for measured resource failure |
| M183 | pending | Fixed ancestor initialization | Keep independent; no HQI combination |

## 4. Gap Analysis
- Need distinguish useful hierarchy evidence from repeated feedback of its own
  earlier selections. In original MQ, retrieved content changes the masks that
  condition the next retrieval at four further boundaries.
- All four unrun topologies share this confound and exceed10G. Releasing their
  holds would violate the goal, and reducing widths/layer_num would be tuning.
- Replace recurrence with a terminal-readout boundary: first five decoder
  predictions have no MQ input; their final mask conditions one context read
  after the final encoder and before the final decoder. No intermediate
  prediction has already consumed retrieved context.
- Nominal reserve becomes1 after withdrawal; capacity4 requires5 eligible.

## 5. Design Rationale
- M184 subtree: test if a coherent coarse region needs all descendant parts.
- M185 path posterior: test complete-path uncertainty without recursive updates.
- M186 hierarchy transport: test coarse mass inheritance at terminal readout.
- M187 frontier: test one fine representative per medium branch at readout.
- These are explicit recurrence-structure ablations of unrun topologies, not
  claims that failed parent results improve. All parent weights/modules/config
  numbers are unchanged; the intervention removes four feedback edges.
- The final boundary derives from the last supervised prediction, not a swept
  layer index. No comparison across arbitrary injection indices is planned.
- Success supports terminal hierarchy context; failure closes that topology
  without trying numerical depth/weights. M183 independently probes initial
  context. Actual full-model resource tests gate all four replacements.

## 6. Next Batch
See designs/exp_design_20260908-1917.md. No active global reservation exists in
goal constraints or the latest ten decision originals. Resource holds are local
to old candidates; active-run disposition remains a logged pending question.
================================================================================
