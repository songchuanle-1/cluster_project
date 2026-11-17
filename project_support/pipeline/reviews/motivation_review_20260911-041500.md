================================================================================
  Motivation Review - cluster_project
  2026-09-11 04:15 Asia/Shanghai
================================================================================

## 1. Goal
Required checker04:08:15: Phase1 NOT YET, ledgerchampion.5020/target.5100/gap+.0080.
Complete authoritative goal snapshot follows;12constraints/11bans unchanged.
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
| Historical context platform improves reference | Descriptive support | Exact M95 .5024607182 vs baseline .4894491136 | Seed fragility; not new novelty |
| Terminal transport beats champion | Unsupported for M186 | .4944996834@17, normal stop27 | Does not explain errors |
| Fixed checkpoint diagnosis is feasible | CPU compatibility verified | Two metadata/log/weight audits | GPU prediction replay and bank collector pending |
| Shared-anchor mechanism addresses measured bottleneck | Provisional | Derivation memo only | No measured errors or verified novelty |

## 3. Experiment Assessment
| Experiment | Exact mIoU | Epoch | Paired Acc50/spmIOU | Evidence role |
|------------|------------|-------|--------------------|---------------|
| Baseline archive20260627_174353 | .4894491136074066 | 15 | .541/.451 | Fixed checkpoint matches log; old analyses misstate epoch/Acc50 |
| M95 archive20260815_101011 | .5024607181549072 | 16 | .557/.465 | Exact checkpoint metric above ledger .5020, still below target |
| M183 | .49154922366142273 | 14 | .545/.455 | Closed tested initialization |
| M186 | .49449968338012695 | 17 | .548/.459 | Closed tested transport; no automatic successor |
| M184/M185/M187/M188 | unfinished | ongoing | live snapshot | Preserve, not final efficacy evidence |
Ledger222rows and224analysis files unchanged. All223 older hashes from
inventory20260910-1324 match; M186 was already analyzed last tick.
This is a supplemental audit, not a new experiment or a rewritten historical result.

## 4. Gap Analysis
- CPU-only worker imported explicit modules, not current automatic fallback.
  Baseline config really was configs/Quard/model_base2.yaml in launch log.
  framework.model.Quard_model.model_base1 fits its learned state; legacy
  model_base2/model_base2 dec.py differs at language-to-instance encoder attention.
  Package naming alone is not historical forward proof; no archived June code
  commit is available in the local git history (initial commit July14).
- Both raw strict loads fail on exactly text_encoder.embeddings.position_ids
  and token_type_ids. Both saved int64[1,514] buffers equal runtime buffers.
  Omitting ONLY these two in memory gives strict load success; no checkpoint
  writes, weight reshaping, missing learned tensors or nonfinite tensor values.
- CUDA_VISIBLE_DEVICES empty; torch.cuda.is_initialized false in both audits.
  One CPU thread, sequential workers; no GPU inference or optimizer steps.
- Checkpoint SHA256 baseline:
  dbc37e8fe8428f0f295121df61fae8a9ffd7dd98c10913ef911354345ff16745.
  M95:fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e.
- Metadata baselineepoch15/best.4894491 and M95epoch16/best.5024607 agree
  with full logs to metadata precision. Exact gain=.01301160455 and
  gap=.00753928185. These are historical audit values, NOT a fresh replay.
  Required goalchecker still uses unmodified ledger .5020/.4894.
- Audit JSONs and two full logs copied locally and SHA-verified; package
  per-file hashes, shapes, full saved YAML and all validations recorded.
- Frozen v2 manifest unchanged:284diagnostic descriptions/71physical scenes;
  4646reserved descriptions/70scenes. Scene sets disjoint; historically reused
  validation is not an independent test set. No new sample selection.
- D1 full candidate masks, selected index, superpoint mapping and GT need an
  isolated collector. Existing predict output returns selected mask only.
  State compatibility does not prove forward equivalence, dataset identity
  across historical dates, numerical replay or error prevalence.

## 5. Design Rationale
Q1: Need reliable baseline/champion replay before diagnosing mask-bank limitation
versus oracle selection gap. Unsupported model fallback could invalidate comparison.
Q2: Explicit import plus exact-buffer-only compatibility removes silent partial
weight loading from the next diagnostic protocol; requires replay, not assumed success.
Q3: D1 should report selected/oracle IoU on the same bank and frozen sample,
then decide ONE mechanism using errors, derivation and verified primary papers.

Coverage: D0 provenance advanced; D1 measurement pending; core derivation and
novelty remain provisional; matched comparison has verified state compatibility
but no predictions; robustness scene split frozen; resource-limited inference
must be checked before any GPU worker. No new numerical configuration or graph.
All12 constraints/11bans retained, no tuning, routing/gates/residuals/repeated
injection, extra seeds, new datasets, schedule changes or resource waiver.

## 6. Next Batch
No new exp_design/model/enqueue: waiting4<capacity4+1 triggers review, but no
new mechanism passes scientific admission. Next productive step: isolated D1
candidate-bank collector with explicit audited modules and buffer checks,
bounded GPU preflight and replay diagnostics; do not edit active packages.
Preserve M189/M190/M191/M193 FIFO and all four running trainers.
Artifacts: reports/d0_checkpoint_identity_20260911-0413/verified_summary.json,
d0_baseline_identity_20260911.json, d0_m95_identity_20260911.json and full logs.
================================================================================
