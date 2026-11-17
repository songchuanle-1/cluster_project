# Motivation Review - cluster_project
Tick #20260913-061000

## 1. Goal
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
check_goal 06:08:13: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072; exact gap .0075392818450928.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context benefit | historical | M95 vs baseline | Derived new mechanism |
| Wrong-instance selection | exploratory | Existing D1/D2 | Independent confirmation |
| Terminal controls improve M95 | unsupported | M184-M190 0/7 | M191/M193 running |
| Positive label guarantees mask success | false as identity | Source and frozen fixture | No causal supervision claim |

## 3. Experiment Assessment
All 231 analyses read and hash-identical to prior tick; all
228 ledger rows read. No new terminal result.
| Experiment | mIoU | State | Motivation Assessment |
|------------|------|-------|-----------------------|
| model_base1_quard2_c2f_enc_lite_posA_l1 | 0.5012 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_posA | 0.5009 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_l1 | 0.5006 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_nomask | 0.4997 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite | 0.4992 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_l3 | 0.4981 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_noroute | 0.4972 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_gbcr_langc2f_scale_l1 | 0.4967 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_cag | 0.4962 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_gbcr_adaptive_l1 | 0.4961 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_gbcr_langroute_l1 | 0.4956 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_posB | 0.4953 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_gbcr_balanced_l1 | 0.4952 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_posC | 0.4952 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_gbcr_langc2f_l1 | 0.4950 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_init0 | 0.4949 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_gbcr_local_l1 | 0.4943 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_l4 | 0.4931 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_posA_l1_layerscale | 0.4921 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_cfe | 0.4901 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1 | 0.4894 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc | 0.4891 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_pq | 0.4864 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_gbcr_pointgate_l1 | 0.4841 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_posA_l1_noroute | 0.4800 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_topk_c2f_bottleneck_l1 | 0.4794 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_cluster_fixed_ctx_l1_ls | 0.4790 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_cluster_fixed_ctx_l1 | 0.4760 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_attnpool | 0.4711 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base2_quard2_c2f | 0.4690 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_posenc | 0.4689 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base2_quard2_c2f_enc | 0.4664 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base2_quard2_l1 | 0.4655 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base2_quard2_c2f_enc_gm1 | 0.4652 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base2_quard2_c2f_pq | 0.4646 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base2 | 0.4641 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base2_quard2_nomask | 0.4633 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base2_quard2 | 0.4598 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_posA_l1_true_route | 0.4468 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_cluster_hier_add_l1 | 0.4041 | done_complete | Historical; individual terminal analysis remains authoritative |
| model_base1_cluster_hier_content_l1 | 0.3659 | done_complete | Historical; individual terminal analysis remains authoritative |
| C1-layerscale | 0.4998 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| D1-detail | 0.4979 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| D1-detail | 0.5003 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| E4-res_detail | 0.4944 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| A4-shuffle | 0.4941 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M1-QGC | 0.4939 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M6-QSF | 0.4866 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M17-ORT | ? | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M16-CSR | 0.4875 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M18-S2FM | 0.4933 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M19-S2FC | 0.4944 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M17-ORT | 0.5005 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M20-DET | 0.4955 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M22-XCA | ? | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M22-XCA | 0.4954 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M21-HYB | 0.4898 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M23-CMX | 0.4910 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M24-ORT-D | 0.4955 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M25-REF | 0.4892 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M26-ORT-HYB | 0.4998 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M27-ORT-W5 | 0.4959 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M28-ORT-W1 | 0.3916 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M33-DTW | 0.4968 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M32-DRP | 0.5012 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M34-Q2P | 0.4904 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M38-FLM | 0.4865 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M39-C2C | 0.4865 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M41-CTF | 0.4995 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M40-SWI | 0.4970 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M42-WCA | 0.4890 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M43-CLN | 0.4930 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M45-NCR | 0.4980 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M46-SHC | 0.4946 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M44-CSF | 0.4958 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M47-FILM | 0.4936 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M48-BIL | 0.4919 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M49-NLR | 0.4948 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M56-DOT | ? | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M57-DET-ORT | ? | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M50-DGC | 0.4913 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M51-DCA | 0.4893 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M55-SCF | 0.4927 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M59-DET-QSF | 0.4961 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M60-DET-CSF | 0.4973 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M61-SCT | 0.4854 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M62-ORTG | 0.4979 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M63-PSR | 0.4964 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M64-SSP | 0.4928 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M54-SAC | 0.4892 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M53-VAC | 0.4889 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M52-CCR | 0.4948 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M66-DET-HCG | 0.4955 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M69-ITER | 0.4978 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M71-CCP | 0.4934 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M58-DET-DRP | 0.498 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M67-PSR-HCG | 0.496 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M68-SSP-HCG | 0.4965 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M73-CCP-DET | 0.4952 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M81-CTF-HCG | missing | waiting | Historical; individual terminal analysis remains authoritative |
| M82-DET-CTF | missing | waiting | Historical; individual terminal analysis remains authoritative |
| M83-DET-REAG-CASC | missing | waiting | Historical; individual terminal analysis remains authoritative |
| M84-DET-CTF-HCG | missing | waiting | Historical; individual terminal analysis remains authoritative |
| M74-CCP-HCG-DET | 0.4948 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M78-REAGG-HCG | 0.5008 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M80-REAG-CASC-HCG | 0.4965 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M81-CTF-HCG | 0.5012 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M82-DET-CTF | 0.4989 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M83-DET-REAG-CASC | 0.3018 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M75-DET-ITER | 0.4956 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M76-DET-REAGG | 0.4909 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M77-ITER-HCG | 0.4933 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M82-DET-CTF | 0.4989 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M83-DET-REAG-CASC | 0.4910 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M84-DET-CTF-HCG | 0.4990 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M85-QMOD | 0.4930 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M88-QMOD-MLAY | 0.4930 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M81-CONS | 0.4950 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M87-DET-CONS | 0.4930 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M90-CTF-HCG-S3 | 0.4940 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M91-HCG-R2 | 0.4960 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M93-CTF-SEF | 0.4910 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| model_base1_quard2_c2f_enc_lite_posA_l1_ctf_sef | 0.4910 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M92-CTF-HCG-ORT | 0.4930 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M94-HCG-ORT | 0.4930 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M89-CTF-HCG-R2 | 0.4980 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M95-CTF-HCG-CSORT | 0.5020 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M96-CTF-HCG-2LAY | 0.4940 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M99-CHAMP-S42 | 0.4930 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M100-CHAMP-S123 | 0.4980 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M102-CTF-HCG-S2026 | 0.4920 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M101-CHAMP-S2026 | 0.4920 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M103-CTF-HCG-CSORT-S2026 | 0.4902 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M98-CHAMP-CSORT | ? | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M104-CTF-HCG-CSORT-S42 | 0.4940 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M105-CTF-HCG-CSORT-S123 | 0.4930 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M106-CHAMP-CSORT-S42 | ? | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M107-CHAMP-CSORT-S123 | ? | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M108-CHAMP-CSORT-S2026 | ? | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M109-CSORT-MSG | 0.5010 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M110-CTF-HCG-MEMBANK | missing | waiting | Historical; individual terminal analysis remains authoritative |
| M111-CTF-HCG-SRL | missing | waiting | Historical; individual terminal analysis remains authoritative |
| M98-CHAMP-CSORT | N/A | crashed | Historical; individual terminal analysis remains authoritative |
| M106-CHAMP-CSORT-S42 | N/A | crashed | Historical; individual terminal analysis remains authoritative |
| M107-CHAMP-CSORT-S123 | N/A | crashed | Historical; individual terminal analysis remains authoritative |
| M108-CHAMP-CSORT-S2026 | N/A | crashed | Historical; individual terminal analysis remains authoritative |
| M110-CTF-HCG-MEMBANK | 0.4950 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M118-CTF-HCG-LCC | missing | waiting | Historical; individual terminal analysis remains authoritative |
| M97-CHAMP-ORT | 0.4920 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M111-CTF-HCG-SRL | 0.4950 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M112-MEMBANK-S42 | 0.4890 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M112-MEMBANK-S42 | 0.4890 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M86-MLAY | 0.5010 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M122-MLAY-S123 | missing | waiting | Historical; individual terminal analysis remains authoritative |
| M114-MEMBANK-S123 | 0.5010 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M113-SRL-S42 | 0.4920 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M115-CTF-HCG-CCL | 0.4890 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M117-CTF-HCG-BCF | 0.4930 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M116-CTF-HCG-CGA | 0.4930 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M127-DET-DCA | missing | waiting | Historical; individual terminal analysis remains authoritative |
| M128-DET-DCM | missing | waiting | Historical; individual terminal analysis remains authoritative |
| M118-CTF-HCG-LCC | 0.4950 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M119-CTF-HCG-MFP | 0.5020 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M123-CTF-HCG-DCA | 0.4970 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M124-CTF-HCG-DCM | 0.5010 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M127-DET-DCA | 0.4870 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M128-DET-DCM | 0.4990 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M129-MFP-S42 | 0.4870 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M130-MFP-S123 | 0.4960 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M133-DCMV | 0.4950 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M126-MLAY-DCM | 0.4980 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M125-MLAY-DCA | 0.4970 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M134-DUAL | 0.4970 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M135-DCM-S42 | 0.4970 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M136-MLAY-DCMV | 0.4960 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M137-DCMV-S42 | 0.4920 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M138-MLAY-DUAL | 0.4990 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M140-CTF-HCG-CLICA | 0.4970 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M139-MLAY-DUAL-LEGACY | 0.4880 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M141-CTF-HCG-CSIC | 0.4960 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M121-CTF-HCG-MLAY-DET | 0.4950 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M142-CTF-HCG-CLICA-CSIC | 0.4890 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M143-CTF-HCG-OBJG | 0.5000 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M144-CTF-HCG-LQA | 0.4930 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M145-CTF-HCG-CSORT-ALL | 0.4920 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M146-CTF-HCG-CSORT-DET | 0.4970 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M148-CTF-HCG-CSORT-DCM | 0.4990 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M147-MLAY-CSORT | 0.4970 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M120-CTF-HCG-MLAY-S42 | 0.4950 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M149-CTF-HCG-CSORT-SG | 0.4940 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M150-CTF-HCG-CSORT-OWC | 0.4920 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M151-CTF-HCG-CSORT-ODW | 0.4970 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M152-CTF-HCG-CSORT-F1 | 0.4940 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M153-CTF-HCG-CSORT-MFP | 0.5000 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M156-CTF-HCG-CSORT-CP | 0.4950 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M154-CTF-HCG-CSORT-GSC | 0.4930 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M157-CTF-HCG-CSORT-PMD | 0.4990 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M155-CTF-HCG-CSORT-RF | 0.4950 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M159-CTF-HCG-CSORT-GEO | 0.4840 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M158-CTF-HCG-CSORT-PMD-SH | 0.4950 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M161-CTF-HCG-CSORT-MQF | 0.4920 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M162-CTF-HCG-CSORT-MQF-SH | 0.4980 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M122-MLAY-S123 | 0.4940 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M163-CTF-HCG-CSORT-MQC | 0.4899 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M166-CTF-HCG-CSORT-MPF | 0.4899 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M160-CTF-HCG-CSORT-GEO-SH | 0.4910 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M167-CTF-HCG-CSORT-MQX | 0.4910 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M168-CTF-HCG-CSORT-MQD | 0.4900 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M170-CTF-HCG-CSORT-MQR | 0.4970 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M169-CTF-HCG-CSORT-MQB | 0.5000 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M172-CTF-HCG-CSORT-MQS | 0.4970 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M171-CTF-HCG-CSORT-MQCC | 0.4936 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M173-CTF-HCG-CSORT-MQCI | 0.4921 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M164-CTF-HCG-CSORT-MQU | 0.4950 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M165-CTF-HCG-CSORT-MQH | 0.4911 | stopped_unknown | Historical; individual terminal analysis remains authoritative |
| M174-CTF-HCG-CSORT-MQHC | 0.4930 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M177-CTF-HCG-CSORT-MQBC | 0.4963 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M176-CTF-HCG-CSORT-MQSD | 0.4936 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M178-CTF-HCG-CSORT-MQTD | 0.4930 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M175-CTF-HCG-CSORT-MQHF | 0.4968 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M183-CTF-HCG-CSORT-HQI | 0.4915 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M186-CTF-HCG-CSORT-MQHT-TR | 0.4945 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M187-CTF-HCG-CSORT-MQFC-TR | 0.4903 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M188-CTF-HCG-CSORT-MQB-TR | 0.4916 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M185-CTF-HCG-CSORT-MQPP-TR | 0.4884 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M184-CTF-HCG-CSORT-MQST-TR | 0.4876 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M189-CTF-HCG-CSORT-MQBC-TR | 0.4909 | done_earlystop | Historical; individual terminal analysis remains authoritative |
| M190-CTF-HCG-CSORT-MQTD-TR | 0.4890 | done_earlystop | Historical; individual terminal analysis remains authoritative |

## 4. Gap Analysis
Q1: A derived and primary-source-distinct mechanism, matched controls,
predefined subsets, scene uncertainty, robustness and efficiency remain open.
M191 platform and M193 full-patience comparison limits remain.

## 5. Design Rationale
Q2: Trace the prior discordant case to current assignment source and frozen
query labels. Q3: Exclude a false label-parser diagnosis without new training.
All 568 rows obey target-membership union nearest; all 42 fixture joins agree.
All12 constraints and11 bans checked: no model, numeric, seed, schedule,
resource-policy or deployment change. No primary-source review this tick.
Scientific admission overrides depth; no generic selector/pooling successor.

## 6. Next Batch
No admitted candidate; no exp_design, implementation, enqueue or sync.
Preserve M191/M193 patience10. Diagnostic: reports/tick_evidence_20260913-061000/diagnostic.md.
