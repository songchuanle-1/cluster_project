================================================================================
  Motivation Review - cluster_project
  2026-09-11 03:19 Asia/Shanghai
================================================================================

## 1. Goal
Target .5100; champion M95 .5020; gap+.0080. Phase1 NOT YET at03:14:52.
Complete goal.json snapshot (12 constraints / 11 bans, no changes):

```json
{
  "metric": {
    "name": "mIoU",
    "target": 0.51,
    "dataset": "ScanRefer"
  },
  "baseline_experiment_id": "model_base1",
  "description": "cluster: 面向 ScanRefer 三维语言定位的具体错误，研究有核心新颖性、可推导且可证伪的轻量结构机制，目标 mIoU ≥ 0.51。多尺度 cluster context 是已有研究基础，不再把变更 pooling、selector、回写位置或变体数量当作研究主线。先诊断候选覆盖与边界、同类目标辨别与关系绑定、多尺度证据重复等问题，再依据证据选择一个核心机制；覆盖机制对照、泛化稳健性和效率验证。共享参照物一致性仅为待验证候选，不预设为最终方向。既有 context/routing 结果是历史证据，不等于新机制已获验证。",
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
    "效率测量: bs=1 warmup20 repeat100 median/P90; 实测延迟/显存为主, FLOPs 为辅",
    "【用户 2026-09-10·后续实验涉及面】新增研究必须覆盖: 错误诊断、核心机制与公式推导、原始文献新颖性核对、机制匹配对照、泛化与稳健性、效率。先用固定样本及已有 checkpoint 诊断候选覆盖/边界、同类辨别/关系绑定、多尺度证据重复；报告分母、样本清单和缺失数据，不凭总体 mIoU 猜瓶颈。依据诊断选择一个主机制，不把多个候选问题同时变成变体队列。操作细则见 docs/experiment_scope_20260910.md；本文件为约束主源。",
    "【用户 2026-09-10·新设计准入】每项新增核心机制需明确具体错误及证据、变量与假设、目标或约束到 forward/loss 的逐步推导、梯度/退化情况/复杂度、与已核实原始论文及历史失败变体的差异、匹配对照和预先否决条件；未核实项必须标为未完成。诊断/复现/对照不要求各自新颖，但必须关联核心问题，不能冒充独立创新。先 motivation_review 再 exp_design，沿用模板并补充这些字段；未完成科学准入的机制不得训练入队。",
    "【用户 2026-09-10·执行优先级】新设计科学准入优先于队列深度补足。没有合格候选时继续数据诊断、推导、原始文献核对或离线正确性检查，记录缺口，不为填满 GPU 批量扩展 selector/pooling/回写变体。非全局暂停，不改 cron 或现有运行状态；已入队 M188/M189/M190/M191/M193 保留原 FIFO 和原准入，定位为旧路线验证，不自动生成后继同类变体。",
    "【用户 2026-09-10·验证边界】主机制须报告总体指标和预先定义的错误子集/负对照；按场景统计不确定性，禁止用测试集选机制。oracle 只用于诊断上界，不作为可部署结果。泛化/稳健性纳入设计，但不自动授权新数据集训练、额外标注或多 seed 扫描；Phase1 首筛 seed1999 和既有 schedule/资源/banned 保持，Phase2 达标后仍先提交确认方案。未验证的效果与新颖性不得写成结论。"
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

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Existing context benefits the original platform | Historical support | A1 .5012 vs .4894 | Not a new contribution |
| Terminal hierarchy transport improves champion | Not supported in this run | M186 .4944996834@17, normal stop27 | Does not identify failure cause |
| Shared physical anchors solve observed errors | Provisional | Mathematical memo only | No measured failure prevalence or verified novelty |
| Candidate quality versus selection is diagnosable | Data access partially verified | D0 inventory and frozen manifest v2 | Need full candidate-bank outputs and verified checkpoints |

## 3. Experiment Assessment
| Experiment | mIoU | Relation to motivation | Contribution |
|------------|------|------------------------|--------------|
| Baseline model_base1 | .4894 | Historical reference | Folder contains model_base2.yaml; checkpoint/config identity needs audit |
| M95 | .5020 | Best recorded platform | Seed and historical patience limitations, not a robust mechanism proof |
| M169 | .5000 | Parent clue for legacy M188 | Compromised patience prevents clean full-run comparison |
| M183 | .4915492237 | Fixed ancestor initialization | Below champion; close tested variant |
| M186 | .4944996834 | Terminal transport | +.0050996834 baseline, -.0075003166 champion; close tested variant |
| M184/M185/M187/M188 | unfinished | Existing admitted legacy controls | Preserve, no efficacy conclusions |
All223 historical analysis hashes matched inventory20260910-1324; one new M186
analysis gives224 files, not224 independent experiments. Ledger222rows includes
historical duplicates/placeholders. Original analyses preserved, not rewritten.

## 4. Gap Analysis
- D0 source: existing remote ScanRefer_val_new.json;9508 unique compound IDs,
  141scan IDs/141physical scene prefixes. All141 required refer.pth files exist.
- Authoritative sample_manifest_v2.json:71 diagnostic physical scenes/284
  descriptions (four per scan);70 reserved scenes/4646 descriptions. Other4578
  diagnostic-scene descriptions are unsampled, not moved into evaluation.
- Split and within-scene sampling use fixed SHA256 ordering before prediction.
  v1 preserved but superseded before any inference. v2 uses physical scene
  grouping defensively; this annotation subset actually has one scan per prefix.
- ManifestSHA25684a7d60f85ecd5bec44b77b304140ff00c8c1fa00177dc12ecf7ef5ebfabb468.
- AnnotationSHA2564455b8857ade37aaafa32581537a961a77bcc756b22d8143ed4021bc88b7931f.
- Champion best/last checkpoint files exist (936269892bytes each); candidate
  baseline best/last exist (854106664bytes). Contents/metadata not loaded yet.
  Baseline saved YAML naming discrepancy must be resolved before matched evaluation.
- No prediction exports found in the two inspected run directories through depth4.
  This is scoped absence, not a global assertion that exports do not exist anywhere.
- tools/test.py saves selected masks; M95 network.predict_by_feat selects
  argmax softmax(indis) and returns only the chosen point mask. Full bank required
  for o=max IoU is unavailable in these returned outputs.
- No error frequencies, oracle values, boundary labels or causal bottleneck measured.
- Prospective reserved validation is historically reused, not an untouched test set.
  Equal-scene samples cannot be reported as population-weighted prevalence.

## 5. Design Rationale
Q1: Missing quantified errors, verified checkpoint identity and full bank outputs.
Q2: D0 first freezes evidence sources and samples; next audit checkpoint metadata
and use an isolated evaluation collector without modifying active model packages.
Q3: D1 will distinguish bank limitation from selection headroom; only then choose
one mechanism, derive it and verify primary papers. No novelty claim here.

Coverage: diagnosis=D0 partial/D1 pending; derivation=provisional memo, not admitted;
novelty=unverified; matched controls=baseline identity pending; robustness=scene
separation frozen, perturbations pending; efficiency=legacy admission retained,
new mechanism profiling not applicable. Inference capacity and memory must be
checked before a bounded evaluation worker; no extra trainer authorized.

All12 constraints and11 bans remain binding: no tuning, schedule/seed changes,
gates, explicit/language routing, residual/repeated injection, N^2 attention or
resource exemption. No proposed new graph passes scientific admission this tick.

## 6. Next Batch
No new exp_design or training enqueue: scientific admission overrides waiting4
versus capacity4+1. Continue D0 checkpoint provenance, then D1 candidate-bank
collector and error measurement on the frozen diagnostic sample.
No automatic sibling pooling/selector/readback family, no multiseed campaign,
new dataset, external annotation API or Phase2 work. Preserve M189/M190/M191/M193.
Artifacts: reports/d0_inventory_20260911-0316/{inventory.json,sample_manifest_v2.json}.
================================================================================
