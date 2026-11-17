"""Persist tested R2 evidence and an explicit, ungranted revision request."""
import ast
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from control import c, OLD, OUT, ROOT

owner, _ = c.guard(240)
result = c.tick.load(OUT / 'combined_candidate_result.json')
baseline = c.tick.load(OLD / 'resources_champion_result.json')
original = c.tick.load(OLD / 'resources_candidate_result.json')
revision1 = c.tick.load(OLD / 'implementation_r1/resources_candidate_result.json')
assert result['execution_completed'] and result['resources_execution_completed']
assert result['graph_controls_passed'] and result['operator_equivalence_passed']
assert result['maximum_operator_error'] == 0
assert result['all_full_source_controls_passed'] is False
assert result['input_sha256'] == baseline['input_sha256'] == original['input_sha256'] == revision1['input_sha256']
assert result['gradient_tensor_count'] == 642 and result['all_observed_gradients_finite']
package = ROOT / 'Cluster/framework/model/Quard_model' / (c.NAME + '_pce')
config = ROOT / 'Cluster/configs/Quard/ctf_hcg_csort_pce' / (c.NAME + '_pce.yaml')
files = sorted(package.glob('*.py'))
for path in files:
    ast.parse(path.read_text(encoding='utf-8'))
expected = c.tick.load(OUT / 'native_manifest.json')['candidate_source_hashes']
assert {path.name: c.tick.digest(path) for path in files} == expected
assert config.stem == package.name

static = c.save('static_independence.json', {
    'observed_at': c.now(), 'candidate_id': c.CID, 'revision': 2,
    'python_files_parsed': len(files), 'unique_config_and_package_basename_match': True,
    'source_sha256': expected, 'config': c.evidence(config),
    'production_loader_status': 'Not deployed; no production-loader/launch success claimed.',
    'no_new_parameters': result['parameters'] == baseline['parameters'],
    'optimizer_steps': 0})

analysis = c.save('analysis.json', {
    'observed_at': c.now(), 'candidate_id': c.CID, 'revision': 2,
    'previous_tick': {'token': 'fefdcc2a82294674927257b9c68f7b47', 'status': 'INCOMPLETE',
        'receipt': c.evidence(ROOT / 'pipeline/tick_receipts/fefdcc2a82294674927257b9c68f7b47.json'),
        'release_verified': '2026-10-20T14:56:19.6655331+08:00; no owned lease/pending remained'},
    'same_resource_input_sha256': result['input_sha256'],
    'resource_table': [{'name': name, 'flops_g': value['profile']['flops_g'],
        'median_ms': value['median_ms'], 'p90_ms': value['p90_ms'],
        'peak_allocated_bytes': value['peak_allocated_bytes'],
        'peak_reserved_bytes': value['peak_reserved_bytes']} for name, value in
        [('M95_reference', baseline), ('PCE_original', original), ('PCE_R1_failed', revision1), ('PCE_R2', result)]],
    'speedup_vs_original': original['median_ms'] / result['median_ms'],
    'latency_reduction_fraction_vs_original': 1 - result['median_ms'] / original['median_ms'],
    'latency_ratio_vs_M95': result['median_ms'] / baseline['median_ms'],
    'peak_allocated_ratio_vs_M95': result['peak_allocated_bytes'] / baseline['peak_allocated_bytes'],
    'flops_caveat': 'Historical FVCore handlers unchanged; added elementwise/sum/softmax work is unsupported, so equal counted total does not mean zero added work.',
    'graph_controls': result['graph_controls'],
    'operator_equivalence': {'passed': True, 'maximum_error': 0.0, 'expressions': 8,
        'scope': 'Same old2TRAINscenes/8expressions, outputs/input gradients/row/deleted/rotated controls; not new population samples.'},
    'full_source_controls': result['controls'], 'full_source_passed': False,
    'full_source_max_error': result['maximum_full_source_control_error'], 'frozen_tolerance': 1e-6,
    'source_scope': result['source_scope'],
    'native_backward': {'completed': True, 'parameter_gradients': 642, 'all_finite': True,
        'real_inst_feats_change_vs_deleted': result['native_feature_path_change_vs_deleted'],
        'optimizer_steps': 0, 'native_loss_forwards_this_tick': result['native_loss_forwards'],
        'native_criterion_backwards_this_tick': result['native_criterion_backwards']},
    'gate_review': {'diagnosis': 'Prior physical cross-leaf information gap remains; task benefit unproved.',
        'controls': 'FAIL full-source1e-6 despite exact graph/operator controls.',
        'native_backward': 'Finite native loss/backward and active inst_feats path verified.',
        'resources': 'Counted10G and matched inference memory met; full latency17.4xM95 remains costly and Pareto review unresolved.',
        'independence': 'Independent source/config checked and native body executed; production deployment not attempted.',
        'constraints': 'All existing bans/seed/schedule/gates retained; no scientific admission.'},
    'scientific_admission': False, 'new_training': 0,
    'unknown': ['Trained efficacy/novelty/generalization', 'Full optimizer-state training peak',
        'Original no-cluster baseline resource delta', 'Population harm and evaluation noise floor'],
    'next_action': 'Ask once for a scoped extra implementation revision; keep original numerical threshold and all failures. No automatic revision3 or training.'})

scope = [c.evidence(path) for path in files] + [c.evidence(config)]
request = c.save('pending_revision3_request.json', {
    'recorded_at': c.now(), 'candidate_id': c.CID, 'current_revision': 2,
    'authorization_granted': False, 'human_reply': None,
    'reason': 'Two preregistered revisions are exhausted. R2 still fails frozen full-source1e-6 and remains latency-heavy despite exact graph/operator repair.',
    'requested_operation': 'One additional bounded PCE implementation revision, restricted to contact-graph construction and source numerical consistency; preserve the same mechanism, numeric threshold, dtype, bans,seed1999/schedule/data and resource gates.',
    'current_file_bundle': scope,
    'not_requested_or_granted': ['No code commit/push', 'No admission waiver', 'No exploratory training exception',
        'No change to goal, scheduler, foreign jobs, GPU allocation, old candidates or historical failures'],
    'human_question': '是否允许 PCE 再做一次局部实现修订，只处理已定位的建图开销和数值一致性，所有原门槛保持不变？',
    'response_contract': 'An unambiguous human reply in owning chat suffices; never require a magic phrase or user-authored JSON.'})

work = c.tick.load(ROOT / 'pipeline/research_work.json')
candidate = next(item for item in work['candidates'] if item['id'] == c.CID)
assert len(candidate['revision_history']) == 2
revision = candidate['revision_history'][1]
revision['result'] = 'failed'
revision['evidence'] = [c.evidence(OLD / 'implementation_revision2.json'),
    c.evidence(OUT / 'combined_candidate_result.json'), c.evidence(analysis), c.evidence(static)]
candidate.update(stage='blocked', scientific_admission=False, failure_scope='implementation',
    blocker_kind='human_revision_authorization',
    blocker='After two bounded revisions, exact graph/operator and native backward pass but full-source error2.86102294921875e-6>1e-6 and588.4056ms latency remain. A third code revision requires scoped human permission; no missing GPU authorization is alleged.',
    retry_after=(datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
    unblock_condition='An explicit human reply authorizes one additional bounded SAME-PCE implementation revision within pending_revision3_request.json. A timer, free GPU, heartbeat or continue-design record is not consent.',
    next_action='Ask once in owning chat for the scoped extra PCE implementation revision. Preserve all failed evidence, current source hashes and original gates. No automatic revision3/commit/push/queue/training; existing GPU permissions remain adequate.',
    wake_paths=['pipeline/authorizations/pce_revision3_approval.json'])
for path in (analysis, static, request, Path(__file__), OLD / 'evaluation_plan.json'):
    item = c.evidence(path)
    if item not in candidate['evidence']:
        candidate['evidence'].append(item)
work['design_cycle'] = {'stop_reason': 'external_resource_blocked',
    'attempted_ids': [c.CID], 'evidence': [c.evidence(analysis), c.evidence(request)],
    'blocker_scope': 'human_revision_authorization; not a physical GPU or connection block',
    'resume_condition': candidate['unblock_condition'],
    'details': 'Only PCE third-revision permission is pending. Old numerical IDs have no new justified control-preserving repair and were not replayed; auxiliary supervision holds unchanged. Preparation reserve is full; no fake free-GPU block or new placeholder design.'}
c.tick.save(ROOT / 'pipeline/research_work.json', work)

stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d-%H%M%S')
decision = ROOT / 'pipeline/decisions' / (stamp + '_next_batch.md')
decision.write_text('# cluster_project 决策记录\n\n- **时间**: ' + stamp + ' Asia/Shanghai\n'
    '- **类型**: next_batch\n- **问题**: PCE修订2是否已可开训？\n'
    '- **决策**: 保留同一候选；图和算子精确等价、完整反向有限，但完整源码数值门槛失败且延迟仍高。未入队、未启动；提出一次有范围的第三次实现修订确认，不索要重复GPU授权。\n'
    '- **依据**: 原型901.2897ms至修订2的588.4056ms，M95为33.7900ms；峰值均936763392bytes；原数值阈值1e-6未变，实测最大2.8610e-6。\n'
    '- **证据**: ' + c.evidence(analysis)['path'] + '\n', encoding='utf-8')
with (ROOT / 'pipeline/decisions/_index.md').open('a', encoding='utf-8') as stream:
    stream.write('\n| ' + stamp + ' | next_batch | PCE-R2已测试但未准入 | 图/算子等价与反向通过，源码数值失败，待有范围的额外实现修订确认 |\n')
candidate['evidence'].append(c.evidence(decision))
c.tick.save(ROOT / 'pipeline/research_work.json', work)

memory = '''# Codex Research Memory
## Goal And Phase
- Current3259705f09e24e0b90718a29a9015c27,DESIGN,begin2026-10-20T06:58:22Z/deadline07:58:22Z;owner01a04987-fdbe-7301-b2f0-f9b6ab60f74c. Pipeline Disabled.
- Priorfefdcc2a INCOMPLETE: deadline expired before report/finish; abort saved receipt and owned lease/pending absence verified14:56:19Shanghai. Prior658721c0 FINALIZED/PASS. Never reuse old tokens/controllers unchanged.
- GoalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85;target.5100;25constraints/11bans. Point/inst_feats hierarchy mainline,not supervision. Seed1999/epochs50/max_iters70/default10G/Pareto unchanged.
## Champion And Baseline
- Historical M95.5020,baseline.4894,target.5100,gap.0080. M203FLE/M204CPA terminal;no restart. Frozen M95epoch16 remains diagnostic only.
## Active Hypotheses
- hierarchy-cross-leaf-physical-contact-exchange:blocked/human_revision_authorization/scientific_admissionFALSE. Same two prereg revisions exhausted; no automatic revision3.
- Original PCE901.2897ms,R1degreebatched833.8442ms,R2geometry588.4056ms vs matched M9533.7900ms. All same original FVCore9.762532428G and peak936763392bytes; addedops unsupported,not free compute. R2 still17.4xM95.
- R1FAILED: identical forward/deleted/row/rotated outputs but input-gradient error6.7353e-6>1e-6. Same-pointer self-gradient original/revised repeats each0; preserve actual difference,not a noise waiver.
- Profile localized original CPUcontact graph724-921ms vs R1exchange8-9ms. R2restores exact original attention and vectorizes exact full membership/coordinate joins,not a new architecture or tuning.
- R2native graph4272edges exactly equal; synthetic multiowner/two-scene edges5/3 exactly equal. Old/new native-feature outputs AND input gradients all0error on same8expressions. No new independent cohort.
- R2full native criterion backward642finite gradients;real inst_feats change versus deleted.5668866038. Source-bank/fullencoder identity and permutation still fail max2.86102294921875e-6>frozen1e-6; do not call operator PASS full-source PASS.
- Actual full-model R2resources/operator/fullsource/backward have now RUN under fresh lease,not pending anymore. Tested9Pythonfiles/config/hash-bound; no production deployment/queue/optimizer/training.
## Closed Or Failed Directions
- All historical bans and negative records preserved. No gate/language routing/residual/largeQKV/N2/tuning/repeated injection/canonical seed repair/reopenedHDS/FLE/M201/M204.
- Two old numerical IDs remain candidate-specific implementation blocks with no new justified measurement repair;no unchanged replay/global mainline freeze. Four supervision candidates remain auxiliary priority holds.
## Running And Queue
- New begin14:58snapshotactive0/target3,waiting0,budget3,reserve3/2,budget0,pending7/8. No new candidate/admission/queue/training/commit/push/sync or scheduler change.
- 15:04live server4GPU0idle/all3locksavailable;GPU1foreignPID825989 preserved. Server3preflightunreachable,itsGPUoccupationUNKNOWN. OnlyGPU0 used for native tests,exclusive locks; preserve foreign jobs.
## Open Questions And Risks
- Pending revision3 request is NOT consent: one additional SAME-PCE implementation repair limited to graph cost/source numerical consistency,all scientific/resource/data/seed/schedule bans unchanged. Ask once; no magic phrase/user JSON needed. GPUauthorization alreadyadequate.
- Fulloptimizerpeak/original no-cluster resource delta/noise floor/trained gain/population harm/novelty UNKNOWN. Formal timing measured,not lightweight latency PASS. Posttrainingplan frozen in tick_fefdcc2a/evaluation_plan.json.
- Current scientific hold cannot be cleared by new name,freeGPU,oldCPA exploratory permission,timer,changingprecision/threshold or model-authored authorization.
## Last Tick
- Current bundle tick_3259705f: fresh continuation/protocol/manifest,combinedR2 evidence,static independence,analysis,pending request,decision,report notes. Older root bundle retains original/R1 failures and untouched archives.
- At this memorysave finish NOT yet run. Render six-section report,finish only on actualPASS and verifylease/pendinggone;otherwise preserve/abort/release. Do not claim scientific/training success.
- Receiptusage is partial begin->receipt window,unknown until receipt,notbilling;cache alreadyininput/reasoningalreadyinoutput. No post-release writes.
'''
(ROOT / 'pipeline/codex_memory.md').write_text(memory, encoding='utf-8')
notes = c.save('report_notes.json', {'actions': [
    '新租约续做同一PCE修订2，源码/配置与上轮冻结哈希一致；上一轮因截止未收尾而INCOMPLETE/abort，14:56核实释放，未覆盖旧失败。',
    '15:07修订2组合验证真实完成：原生4272条几何边与原版逐边完全相同，共占据/双场景控制也完全相同；同两TRAIN场景8表达的输出、输入梯度、删边、行置换、旋转值误差全0。',
    '相同输入/原FVCore/bs1 warmup20 repeat100：M95中位33.790ms，原PCE901.290ms，R1 833.844ms，R2 588.406ms。R2比原型耗时减少约34.72%，仍约为M95的17.4倍；不能报轻量化延迟通过。',
    '四者原计数均9.762532428G、推理峰值均936763392bytes；计数器未支持新增逐项/sum/softmax，不能把相同FLOPs称为零计算增量。完整optimizer峰值和无cluster原baseline资源差未知。',
    '完整源码层级聚合/编码器对照仍失败：最大2.8610e-6>原1e-6；完整原生loss反向642梯度有限、inst_feats确实变化.5668866，但这不是科学准入或训练收益。',
    '本轮原生loss前向2、完整反向1、整模型predict121；仍复用既有两场景8表达，不计作新人口样本。用量收据仅本轮begin到receipt的局部窗口，当前未知，不重复加缓存/推理，不当账单。',
    '新增训练/入队/优化器步数/提交/推送/生产同步均0；物理GPU不是当前科学阻塞，GPU1外部进程未触碰。'],
    'decisions': [
    '同一候选两次有界实现修订已用完，R1及R2整体未通过记录保留；原假设未被科学证伪。先等待一次有具体范围的额外修订确认，不自动revision3、不改名、不放宽1e-6/10G/seed/schedule。',
    '人工边界阻塞不是缺GPU授权；所需操作与当前9Python文件/独立config哈希记录于pending_revision3_request.json，authorization_granted=false，不要求用户写JSON或固定口令。',
    '按闭环的外部授权边界收尾，旧数值候选无新可区分修复不重复跑，旧监督优先级保留不恢复；不宣称所有独立机制已穷尽。finish仅表示本轮记录闭环，不表示候选有效或已开训。']})
print(json.dumps({'analysis': c.evidence(analysis), 'notes': str(notes), 'scientific_admission': False,
    'training_started': False, 'next_action': candidate['next_action']}, ensure_ascii=False))
